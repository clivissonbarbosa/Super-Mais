from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


StatusPagamento = Literal["pendente", "pago", "cancelado"]


class ContaReceberCreate(BaseModel):
    id_venda: int = Field(gt=0)
    data_vencimento: datetime
    valor: float = Field(gt=0)


class ContaReceberUpdate(BaseModel):
    data_vencimento: datetime | None = None
    valor: float | None = Field(default=None, gt=0)


class ContaReceberOut(BaseModel):
    id_conta_receber: int
    id_venda: int
    data_vencimento: datetime
    valor: float
    status_pagamento: StatusPagamento

    model_config = ConfigDict(from_attributes=True)
