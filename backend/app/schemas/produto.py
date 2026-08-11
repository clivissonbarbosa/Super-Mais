from pydantic import BaseModel, ConfigDict, Field


class ProdutoCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=160)
    id_categoria: int = Field(gt=0)
    codigo_barras: str = Field(min_length=1, max_length=80)
    preco_venda: float = Field(gt=0)


class ProdutoOut(ProdutoCreate):
    id_produto: int

    model_config = ConfigDict(from_attributes=True)
