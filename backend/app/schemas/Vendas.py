from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VendaCreate(BaseModel):
    id_unidade: int = Field(gt=0)
    id_usuario: int = Field(gt=0)
    id_cliente: int | None = None
    id_produto: int | None = None
    data_hora: datetime | None = None
    valor_total: float = Field(gt=0)
    forma_pagamento: str = Field(min_length=1, max_length=50)


class VendaOut(BaseModel):
    id_venda: int
    id_unidade: int
    id_usuario: int
    id_cliente: int | None = None
    id_produto: int | None = None
    data_hora: datetime | None = None
    valor_total: float
    forma_pagamento: str

    model_config = ConfigDict(from_attributes=True)
