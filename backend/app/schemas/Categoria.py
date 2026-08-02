from pydantic import BaseModel

class CategoriaCreate(BaseModel):
   nome: str
   margem_lucro: float

class CategoriaOut(BaseModel):
    id_categoria: int
    nome: str
    margem_lucro: float


    class Config:
        orm_mode = True