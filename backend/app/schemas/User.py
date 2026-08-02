from pydantic import BaseModel

class UserCreate(BaseModel):
    id_unidade: int
    nome: str
    login: str
    senha: str  

class UserOut(UserCreate):
    id_usuario: int
    id_unidade: int
    nome: str
    login: str

    class Config:
        from_attributes = True