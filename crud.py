from sqlalchemy.orm import Session
from models import Image
from schemas import ImageBase   

# Get an image by its UID
def get_image(db: Session, image_id: int):
    return db.query(Image).filter(Image.uid == image_id).first()

# Upload an image to the database
def post_image(db: Session, image: ImageBase):
    db_image = Image(uid=image.uid, image=image.image, authenticationDate=image.authenticationDate)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image
