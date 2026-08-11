from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VendaProdutoCreate(BaseModel):
    id_produto: int = Field(gt=0)
    quantidade: int = Field(gt=0)


class VendaItemOut(BaseModel):
    id_item: int
    id_venda: int
    id_produto: int
    quantidade: int
    preco_unitario: float

    model_config = ConfigDict(from_attributes=True)


class VendaCreate(BaseModel):
    id_unidade: int = Field(gt=0)
    id_usuario: int | None = Field(default=None, gt=0)
    id_cliente: int | None = Field(default=None, gt=0)
    id_produto: int | None = Field(default=None, gt=0)
    data_hora: datetime | None = None
    valor_total: float | None = Field(default=None, gt=0)
    forma_pagamento: str = Field(min_length=1, max_length=50)
    itens: list[VendaProdutoCreate] = Field(default_factory=list)


class VendaOut(BaseModel):
    id_venda: int
    id_unidade: int
    id_usuario: int
    id_cliente: int | None = None
    id_produto: int | None = None
    data_hora: datetime | None = None
    valor_total: float
    forma_pagamento: str
    itens: list[VendaItemOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
