# backend/app/schemas/Unidade.py
from pydantic import BaseModel

class UnidadeCreate(BaseModel):
    nome: str
    tipo: str

class UnidadeOut(UnidadeCreate):
    id_unidade: int
    class Config:
        from_attributes = True