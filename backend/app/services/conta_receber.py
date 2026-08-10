from datetime import datetime, timedelta
from math import isclose

from sqlalchemy.orm import Session

from app.models.Conta_Receber import ContaReceber
from app.models.Fluxo_Caixa import FluxoCaixa
from app.models.Vendas import Venda
from app.schemas.Conta_Receber import ContaReceberUpdate
from app.services import fluxo_caixa_service
from app.services.financeiro_exceptions import RegraNegocioFinanceira


def criar_conta_receber(
    db: Session,
    *,
    id_venda: int,
    valor: float,
    data_vencimento: datetime | None = None,
    prazo_dias: int = 0,
    commit: bool = True,
) -> ContaReceber:
    venda = db.query(Venda).filter(Venda.id_venda == id_venda).first()
    if not venda:
        raise RegraNegocioFinanceira("Venda não encontrada.")
    if valor <= 0:
        raise RegraNegocioFinanceira("O valor da conta deve ser maior que zero.")
    if not isclose(float(valor), float(venda.valor_total), abs_tol=0.01):
        raise RegraNegocioFinanceira("O valor da conta deve ser igual ao total da venda.")
    if db.query(ContaReceber).filter(ContaReceber.id_venda == id_venda).first():
        raise RegraNegocioFinanceira("Já existe uma conta a receber para esta venda.")
    if prazo_dias < 0:
        raise RegraNegocioFinanceira("O prazo de recebimento não pode ser negativo.")

    conta = ContaReceber(
        id_venda=id_venda,
        data_vencimento=data_vencimento
        or fluxo_caixa_service.agora_utc() + timedelta(days=prazo_dias),
        valor=valor,
        status_pagamento="pendente",
    )
    db.add(conta)
    db.flush()
    if commit:
        db.commit()
        db.refresh(conta)
    return conta


def listar_contas_receber(
    db: Session,
    status: str | None = None,
    somente_vencidas: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[ContaReceber]:
    query = db.query(ContaReceber)
    if status:
        query = query.filter(ContaReceber.status_pagamento == status)
    if somente_vencidas:
        query = query.filter(
            ContaReceber.status_pagamento == "pendente",
            ContaReceber.data_vencimento < fluxo_caixa_service.agora_utc(),
        )
    return query.order_by(ContaReceber.data_vencimento).offset(skip).limit(limit).all()


def buscar_conta_receber(db: Session, id_conta_receber: int) -> ContaReceber | None:
    return (
        db.query(ContaReceber)
        .filter(ContaReceber.id_conta_receber == id_conta_receber)
        .first()
    )


def atualizar_conta_receber(
    db: Session, id_conta_receber: int, dados: ContaReceberUpdate
) -> ContaReceber | None:
    conta = buscar_conta_receber(db, id_conta_receber)
    if not conta:
        return None
    if conta.status_pagamento != "pendente":
        raise RegraNegocioFinanceira("Somente contas pendentes podem ser alteradas.")

    alteracoes = dados.model_dump(exclude_unset=True)
    if "valor" in alteracoes:
        venda = db.query(Venda).filter(Venda.id_venda == conta.id_venda).first()
        if not venda or not isclose(float(alteracoes["valor"]), float(venda.valor_total), abs_tol=0.01):
            raise RegraNegocioFinanceira("O valor da conta deve ser igual ao total da venda.")
    for campo, valor in alteracoes.items():
        setattr(conta, campo, valor)
    db.commit()
    db.refresh(conta)
    return conta


def dar_baixa(db: Session, id_conta_receber: int) -> ContaReceber | None:
    """Confirma o recebimento e grava a entrada na mesma transação."""
    conta = (
        db.query(ContaReceber)
        .filter(ContaReceber.id_conta_receber == id_conta_receber)
        .with_for_update()
        .first()
    )
    if not conta:
        return None
    if conta.status_pagamento == "pago":
        return conta
    if conta.status_pagamento == "cancelado":
        raise RegraNegocioFinanceira("Uma conta cancelada não pode receber baixa.")

    try:
        conta.status_pagamento = "pago"
        fluxo_caixa_service.registrar_lancamento(
            db,
            id_conta_pagar=None,
            id_conta_receber=conta.id_conta_receber,
            tipo_lancamento="entrada",
            valor=conta.valor,
            commit=False,
        )
        db.commit()
        db.refresh(conta)
        return conta
    except Exception:
        db.rollback()
        raise


def excluir_conta_receber(db: Session, id_conta_receber: int) -> bool:
    conta = buscar_conta_receber(db, id_conta_receber)
    if not conta:
        return False
    if conta.status_pagamento != "pendente":
        raise RegraNegocioFinanceira("Somente contas pendentes podem ser excluídas.")
    if db.query(FluxoCaixa).filter(FluxoCaixa.id_conta_receber == id_conta_receber).first():
        raise RegraNegocioFinanceira("A conta possui movimentação financeira e não pode ser excluída.")
    db.delete(conta)
    db.commit()
    return True
