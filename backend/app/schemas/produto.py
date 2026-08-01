from pydantic import BaseModel

class ProdutoCreate(BaseModel):
    nome: str
    codigo_barras: str
    preco_venda: float

class ProdutoOut(ProdutoCreate):
    id_produto: int

    class Config:
        from_attributes = True