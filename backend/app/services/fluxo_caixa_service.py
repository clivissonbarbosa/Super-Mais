from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.Conta_Pagar import ContaPagar
from app.models.Conta_Receber import ContaReceber
from app.models.Fluxo_Caixa import FluxoCaixa
from app.services.financeiro_exceptions import RegraNegocioFinanceira


def agora_utc() -> datetime:
    """Retorna UTC sem timezone para manter compatibilidade com DateTime atual."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def registrar_lancamento(
    db: Session,
    *,
    id_conta_pagar: int | None,
    id_conta_receber: int | None,
    tipo_lancamento: str,
    valor: float,
    id_usuario: int | None = None,
    commit: bool = True,
) -> FluxoCaixa:
    """Registra um evento imutável de caixa vinculado a exatamente uma conta."""
    if (id_conta_pagar is None) == (id_conta_receber is None):
        raise RegraNegocioFinanceira(
            "O lançamento deve estar vinculado a uma única conta a pagar ou a receber."
        )
    if valor <= 0:
        raise RegraNegocioFinanceira("O valor do lançamento deve ser maior que zero.")
    if id_conta_pagar is not None and tipo_lancamento != "saida":
        raise RegraNegocioFinanceira("Conta a pagar deve gerar lançamento de saída.")
    if id_conta_receber is not None and tipo_lancamento != "entrada":
        raise RegraNegocioFinanceira("Conta a receber deve gerar lançamento de entrada.")

    query = db.query(FluxoCaixa)
    if id_conta_pagar is not None:
        existente = query.filter(FluxoCaixa.id_conta_pagar == id_conta_pagar).first()
    else:
        existente = query.filter(FluxoCaixa.id_conta_receber == id_conta_receber).first()
    if existente:
        raise RegraNegocioFinanceira("Esta conta já possui um lançamento no fluxo de caixa.")

    lancamento = FluxoCaixa(
        id_conta_pagar=id_conta_pagar,
        id_conta_receber=id_conta_receber,
        tipo_lancamento=tipo_lancamento,
        valor=valor,
        id_usuario=id_usuario,
        data_confirmacao=agora_utc(),
    )
    db.add(lancamento)
    db.flush()
    if commit:
        db.commit()
        db.refresh(lancamento)
    return lancamento


def listar_lancamentos(
    db: Session,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[FluxoCaixa]:
    if data_inicio and data_fim and data_inicio > data_fim:
        raise RegraNegocioFinanceira("A data inicial não pode ser posterior à data final.")

    query = db.query(FluxoCaixa)
    if data_inicio:
        query = query.filter(FluxoCaixa.data_confirmacao >= data_inicio)
    if data_fim:
        query = query.filter(FluxoCaixa.data_confirmacao <= data_fim)
    return (
        query.order_by(FluxoCaixa.data_confirmacao.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def _somar_fluxo(
    db: Session,
    tipo: str,
    data_inicio: datetime | None,
    data_fim: datetime | None,
) -> float:
    query = db.query(func.coalesce(func.sum(FluxoCaixa.valor), 0.0)).filter(
        FluxoCaixa.tipo_lancamento == tipo
    )
    if data_inicio:
        query = query.filter(FluxoCaixa.data_confirmacao >= data_inicio)
    if data_fim:
        query = query.filter(FluxoCaixa.data_confirmacao <= data_fim)
    return float(query.scalar() or 0.0)


def resumo_periodo(
    db: Session,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
) -> dict[str, float]:
    """Consolida caixa realizado e obrigações pendentes para uso gerencial."""
    if data_inicio and data_fim and data_inicio > data_fim:
        raise RegraNegocioFinanceira("A data inicial não pode ser posterior à data final.")

    entradas = _somar_fluxo(db, "entrada", data_inicio, data_fim)
    saidas = _somar_fluxo(db, "saida", data_inicio, data_fim)
    receber_pendente = float(
        db.query(func.coalesce(func.sum(ContaReceber.valor), 0.0))
        .filter(ContaReceber.status_pagamento == "pendente")
        .scalar()
        or 0.0
    )
    pagar_pendente = float(
        db.query(func.coalesce(func.sum(ContaPagar.valor), 0.0))
        .filter(ContaPagar.status_pagamento == "pendente")
        .scalar()
        or 0.0
    )
    receber_vencido = float(
        db.query(func.coalesce(func.sum(ContaReceber.valor), 0.0))
        .filter(
            ContaReceber.status_pagamento == "pendente",
            ContaReceber.data_vencimento < agora_utc(),
        )
        .scalar()
        or 0.0
    )
    return {
        "entradas": entradas,
        "saidas": saidas,
        "saldo": entradas - saidas,
        "contas_receber_pendentes": receber_pendente,
        "contas_pagar_pendentes": pagar_pendente,
        "contas_receber_vencidas": receber_vencido,
    }
