from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from crud import get_image, post_image
from schemas import ImageBase


app = FastAPI()

origins = [
    "http://localhost:5173",
    "localhost:5173"
]

images = {}

# - fetch image by its UID
@app.get('/images/{image_id}')
def fetch_image(image_id: int):
    image = get_image(image_id)
    return image

# - upload an image
@app.post('/images/')
def upload_image(image: ImageBase):
    image = post_image(image)
    return image