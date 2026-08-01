from pydantic import BaseModel

class FornecedorCreate(BaseModel):
    nome: str
    cnpj: str
    endereco: str
    telefone: str

class FornecedorOut(FornecedorCreate):
    id: int

    class Config:
        orm_mode = True