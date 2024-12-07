import os
import uuid
import base64
import tempfile
from models import Image 
from fastapi import HTTPException
from fastapi import FastAPI, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from supabase import create_client, Client
from crud import get_image, post_image
from database import get_db  
from schemas import ImageBase, ImageCreate
from io import BytesIO
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

@app.get("/")
async def welcome():
    return {"message": "Welcome to our API!"}

# - fetch image by its UID
@app.get('/images/{uid}')
async def get_image(uid: int, db: Session = Depends(get_db)):
    # Step 1: Retrieve image metadata (uid, image name, authentication date) from the database
    db_image = db.query(Image).filter(Image.uid == uid).first()

    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found in the database")

    # Step 2: List files in the 'uid' folder to get the image name dynamically
    try:
        # Get a list of all files in the folder named by `uid`
        files = supabase.storage.from_('authenticated-images').list(f"{db_image.uid}/")

        if not files:
            raise HTTPException(status_code=404, detail="No images found in the folder")

        # Assuming only one image exists, get the first file
        image_filename = files[0]['name']  # This assumes the first file is the image you want

        print(f"Fetching image from path: {db_image.uid}/{image_filename}")  # Log the path to debug

        # Step 3: Fetch the image from Supabase storage (this returns raw bytes)
        image_data = supabase.storage.from_('authenticated-images').download(f"{db_image.uid}/{image_filename}")

        if image_data:
            # Step 4: Convert image to base64
            image_data_base64 = base64.b64encode(image_data).decode("utf-8")

            # Step 5: Return both metadata and base64-encoded image
            return {
                "uid": db_image.uid,
                "authenticationDate": db_image.authenticationDate,
                "image_filename": image_filename,  # The dynamically fetched image filename
                "image_data_base64": image_data_base64  # Base64 encoded image data
            }
        else:
            raise HTTPException(status_code=404, detail="Image not found in Supabase storage")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching image: {str(e)}")

@app.post('/images/')
async def upload_image(
    file: UploadFile = File(...),  # The uploaded file
    db: Session = Depends(get_db)
):
    # Extract the original file name
    original_file_name = file.filename

    # Save the image data to the database
    db_image = post_image(db, ImageCreate(image=original_file_name))

    # Generate a unique filename for storage
    file_extension = os.path.splitext(file.filename)[1]
    image_filename = f"{db_image.uid}/{uuid.uuid4()}{file_extension}"

    # Read the file data
    file_data = await file.read()

    # Upload the file to Supabase storage
    try:
        storage_response = supabase.storage.from_('authenticated-images').upload(
            image_filename,
            file_data,
            {'content-type': file.content_type}
        )

        # Debug: print the response to see its structure
        print(storage_response)

        # Assuming the response has a 'path' attribute for the uploaded file location
        if hasattr(storage_response, 'path'):  # If 'path' is available
            return {
                "message": "Image uploaded successfully",
                "image": db_image,
                "file_url": storage_response.path  # Directly access the path
            }
        else:
            return {
                "message": "Error uploading image to Supabase",
                "error": "No path in the response"  # If the response does not contain the 'path'
            }

    except Exception as e:
        return {"message": "Error uploading image to Supabase", "error": str(e)}

