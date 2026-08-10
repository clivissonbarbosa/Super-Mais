from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict


class TipoMovimento(str, Enum):
    ENTRADA = "Entrada"
    SAIDA = "Saída"
    PERDA = "Perda"


# =========================
# ESTOQUE SALDO
# =========================

class EstoqueSaldoBase(BaseModel):
    id_produto: int
    id_unidade: int
    quantidade_atual: int = 0
    estoque_minimo: int = 0


class EstoqueSaldoCreate(EstoqueSaldoBase):
    pass


class EstoqueSaldoUpdate(BaseModel):
    quantidade_atual: int | None = None
    estoque_minimo: int | None = None


class EstoqueSaldoOut(EstoqueSaldoBase):
    id_saldo: int

    model_config = ConfigDict(from_attributes=True)


# =========================
# ESTOQUE MOVIMENTAÇÃO
# =========================

class EstoqueMovimentacaoBase(BaseModel):
    id_produto: int
    id_unidade: int
    tipo_movimento: TipoMovimento
    quantidade: int
    motivo: str | None = None


class EstoqueMovimentacaoCreate(EstoqueMovimentacaoBase):
    pass


class EstoqueMovimentacaoOut(EstoqueMovimentacaoBase):
    id_movimentacao: int
    data_movimentacao: datetime

    model_config = ConfigDict(from_attributes=True)