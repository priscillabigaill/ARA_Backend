from sqlalchemy import Column, Integer, String
# from database import Base

class Image():
    __tablename__ = "images"

    uid = Column(Integer, primary_key=True, index=True)
    image = Column(String, index=True)
    authenticationDate = Column(String, index=True)
