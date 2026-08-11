from pydantic import BaseModel, ConfigDict, Field


class CategoriaCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=120)
    margem_lucro: float = Field(ge=0)


class CategoriaOut(CategoriaCreate):
    id_categoria: int

    model_config = ConfigDict(from_attributes=True)
