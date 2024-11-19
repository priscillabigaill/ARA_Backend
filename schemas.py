from pydantic import BaseModel

class ImageBase(BaseModel):
    uid: int
    image: str
    authenticationDate: str

class Image(ImageBase):
    uid: int

    class Config:
        orm_mode = True
