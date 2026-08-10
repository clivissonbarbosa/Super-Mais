from pydantic import BaseModel
from pydantic import BaseModel

class EstoqueBase(BaseModel):
    quantidade: int
    produto_id: int
    unidade_id: int

    class Config:
        orm_mode = True 

        