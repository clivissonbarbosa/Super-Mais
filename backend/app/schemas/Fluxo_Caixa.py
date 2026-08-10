from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


TipoLancamento = Literal["entrada", "saida"]


class FluxoCaixaOut(BaseModel):
    id_lancamento: int
    id_conta_pagar: int | None
    id_conta_receber: int | None
    tipo_lancamento: TipoLancamento
    valor: float
    data_confirmacao: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumoFinanceiroOut(BaseModel):
    entradas: float
    saidas: float
    saldo: float
    contas_receber_pendentes: float
    contas_pagar_pendentes: float
    contas_receber_vencidas: float
