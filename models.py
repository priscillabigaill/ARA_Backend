# models.py
from sqlalchemy import Column, Integer, String
from database import Base  # Assuming you have a Base object in database.py

class Image(Base):
    __tablename__ = "images"

    uid = Column(Integer, primary_key=True, index=True)
    image = Column(String, index=True)
    authenticationDate = Column(String, index=True)
