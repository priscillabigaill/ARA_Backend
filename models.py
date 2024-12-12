# models.py
from sqlalchemy import Column, Integer, String, Date
from database import Base
from sqlalchemy.sql import func

class Image(Base):
    __tablename__ = 'images'

    uid = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(String(255)) 
    authenticationDate = Column(Date, default=func.current_date()) 