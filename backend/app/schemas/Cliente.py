# backend/app/schemas/cliente.py
from pydantic import BaseModel

class ClienteCreate(BaseModel):
    cpf: str
    nome: str
    segmento_marketing: str | None = None

class ClienteOut(ClienteCreate):
    id_cliente: int
    class Config:
        from_attributes = True