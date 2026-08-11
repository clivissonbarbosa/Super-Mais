from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UnidadeCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=160)
    tipo: Literal["Loja", "CD"]


class UnidadeOut(UnidadeCreate):
    id_unidade: int

    model_config = ConfigDict(from_attributes=True)
