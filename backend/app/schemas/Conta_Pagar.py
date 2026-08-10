from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


StatusPagamento = Literal["pendente", "pago", "cancelado"]


class ContaPagarCreate(BaseModel):
    id_nota: int = Field(gt=0)
    data_vencimento: datetime
    valor: float = Field(gt=0)


class ContaPagarUpdate(BaseModel):
    data_vencimento: datetime | None = None
    valor: float | None = Field(default=None, gt=0)


class ContaPagarOut(BaseModel):
    id_conta_pagar: int
    id_nota: int
    data_vencimento: datetime
    valor: float
    status_pagamento: StatusPagamento

    model_config = ConfigDict(from_attributes=True)
