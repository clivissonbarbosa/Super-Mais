from pydantic import BaseModel

class ProdutoCreate(BaseModel):
    nome: str
    id_categoria: int
    codigo_barras: str
    preco_venda: float

class ProdutoOut(ProdutoCreate):
    id_produto: int
    nome: str
    id_categoria: int

    class Config:
        from_attributes = True