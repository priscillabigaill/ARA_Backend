from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from crud import get_image, post_image
from database import get_db  # Assuming you have a function to get a DB session
from schemas import ImageBase

app = FastAPI()

# - fetch image by its UID
@app.get('/images/{image_id}')
def fetch_image(image_id: int, db: Session = Depends(get_db)):
    image = get_image(db, image_id)
    return image


# - upload an image
@app.post('/images/')
def upload_image(image: ImageBase, db: Session = Depends(get_db)):
    uploaded_image = post_image(db, image)  
    return uploaded_image