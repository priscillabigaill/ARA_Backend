import os
import uuid
import base64
from datetime import datetime
from io import BytesIO
from PIL import Image as PILImage
from sqlalchemy.orm import Session
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from tensorflow.keras.models import load_model
import numpy as np
from dotenv import load_dotenv
from crud import post_image
from database import get_db
from schemas import ImageCreate
from models import Image as ImageModel
import tensorflow as tf

load_dotenv()
tf.compat.v1.enable_eager_execution()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

origins = [
    "http://localhost:5173",
    "https://ara-frontend-coral.vercel.app/"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI models
models = {
    "vgg16": load_model("models/vgg16_model_v1_epoch_20.keras"),
    "vgg9": load_model("models/vgg9_model_v5_epoch_27.keras"),
    "efficientnet": load_model("models/efficientnet_model_v1_epoch_18.keras"),
    "resnet50": load_model("models/resnet50_model_v1_epoch_12.keras"),
    "mobilenet": load_model("models/mobilenet_model_v1_epoch_28.keras"),
}

# Classes for predictions
CLASSES = ["cyclegan", "dalle", "midjourney", "real", "stablediffusion"]


# - fetch image by its UID
@app.get("/images/{uid}")
async def get_image(uid: int, db: Session = Depends(get_db)):
    try:
        # Retrieve metadata from the database
        db_image = db.query(ImageModel).filter(ImageModel.uid == uid).first()
        if not db_image:
            raise HTTPException(status_code=404, detail="Image not found in the database")

        # Check for files in the folder named after the UID
        folder_name = str(db_image.uid)
        files = supabase.storage.from_("authenticated-images").list(folder_name)
        if not files:
            raise HTTPException(status_code=404, detail="No images found in the folder")

        image_filename = files[0]["name"]
        print(f"Fetching image from path: {folder_name}/{image_filename}")

        # Fetch the image from Supabase storage
        image_data = supabase.storage.from_("authenticated-images").download(
            f"{folder_name}/{image_filename}"
        )

        if image_data:
            # Convert image to base64
            image_data_base64 = base64.b64encode(image_data).decode("utf-8")
            return {
                "uid": db_image.uid,
                "authenticationDate": db_image.authenticationDate,
                "image_filename": image_filename,
                "image_data_base64": image_data_base64,
            }
        else:
            raise HTTPException(status_code=404, detail="Image not found in Supabase storage")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching image: {str(e)}")


@app.post("/images/")
async def upload_image(
    file: UploadFile = File(...),
    save_to_db: bool = Form(False),
    db: Session = Depends(get_db),
):
    try:
        # Read file data
        file_data = await file.read()
        original_image = PILImage.open(BytesIO(file_data)).convert("RGB")
        predictions = {}
        all_model_results = {}

        # Process predictions for each model
        for model_name, model in models.items():
            input_shape = model.input_shape[1:3]
            resized_image = original_image.resize(input_shape)
            image_array = np.expand_dims(np.array(resized_image) / 255.0, axis=0)
            pred = model.predict(image_array)
            predictions[model_name] = pred[0]

            model_results = {
                class_name: f"{float(prob) * 100:.2f}%"
                for class_name, prob in zip(CLASSES, pred[0])
            }
            all_model_results[model_name] = model_results

        # VGG16-specific logic
        vgg16_probabilities = predictions["vgg16"]
        ai_generated_probability = (
            vgg16_probabilities[CLASSES.index("cyclegan")]
            + vgg16_probabilities[CLASSES.index("dalle")]
            + vgg16_probabilities[CLASSES.index("midjourney")]
            + vgg16_probabilities[CLASSES.index("stablediffusion")]
        )
        human_generated_probability = 1.0 - ai_generated_probability
        classification = (
            "likely AI-generated"
            if ai_generated_probability > 0.5
            else "likely human-created"
        )

        # Log model predictions
        print("Individual model predictions:")
        for model_name, results in all_model_results.items():
            print(f"Model: {model_name}")
            for class_name, probability in results.items():
                print(f"  {class_name}: {probability}")

        # Save to database (if requested)
        db_image = None
        if save_to_db:
            db_image = post_image(db, ImageCreate(image=file.filename))
            folder_name = str(db_image.uid)
        else:
            folder_name = "temporary"

        # Print the uid and folder name
        print(f"UID: {db_image.uid if db_image else 'N/A'}")
        print(f"Folder name: {folder_name}")
        
        # Upload file to Supabase storage
        file_extension = os.path.splitext(file.filename)[1]
        image_filename = f"{folder_name}/{uuid.uuid4()}{file_extension}"
        storage_response = supabase.storage.from_("authenticated-images").upload(
            image_filename, file_data, {"content-type": file.content_type}
        )

        file_url = (
            storage_response["path"]
            if isinstance(storage_response, dict)
            else storage_response
        )

        return {
            "message": "Image processed successfully",
            "classification": classification,
            "real_image_probability": f"{human_generated_probability * 100:.2f}%",
            "ai_generated_probability": f"{ai_generated_probability * 100:.2f}%",
            "file_url": file_url,
            "all_model_results": all_model_results,
            "saved_to_database": bool(db_image),
            "uid": db_image.uid if db_image else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

