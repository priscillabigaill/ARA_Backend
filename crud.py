from sqlalchemy.orm import Session
from models import Image
from schemas import ImageBase, ImageCreate    

# Get an image by its UID
def get_image(db: Session, image_id: int):
    return db.query(Image).filter(Image.uid == image_id).first()

# Upload an image to the database
def post_image(db: Session, image_data: ImageCreate):
    db_image = Image(image=image_data.image)  # Pass the file name
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image