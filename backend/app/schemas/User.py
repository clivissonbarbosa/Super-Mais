from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserOut(UserCreate):
    id: int
    balance: float

    class Config:
        from_attributes = True