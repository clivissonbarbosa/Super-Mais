from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TipoMovimento = Literal["entrada", "saida", "perda"]


class EstoqueSaldoOut(BaseModel):
    id_saldo: int
    id_produto: int
    id_unidade: int
    quantidade_atual: int
    estoque_minimo: int

    model_config = ConfigDict(from_attributes=True)


class EstoqueMinimoUpdate(BaseModel):
    estoque_minimo: int = Field(ge=0)


class EstoqueMovimentacaoCreate(BaseModel):
    id_produto: int = Field(gt=0)
    id_unidade: int = Field(gt=0)
    tipo_movimento: TipoMovimento
    quantidade: int = Field(gt=0)
    motivo: str | None = Field(default=None, max_length=255)


class EstoqueMovimentacaoOut(EstoqueMovimentacaoCreate):
    id_movimentacao: int
    id_usuario: int | None = None
    data_movimentacao: datetime
    referencia_tipo: str | None = None
    referencia_id: int | None = None

    model_config = ConfigDict(from_attributes=True)
