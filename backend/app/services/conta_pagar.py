from datetime import datetime, timedelta
from math import isclose

from sqlalchemy.orm import Session

from app.models.Conta_Pagar import ContaPagar
from app.models.Fluxo_Caixa import FluxoCaixa
from app.models.Nota_Fiscal import NotaFiscal
from app.schemas.Conta_Pagar import ContaPagarUpdate
from app.services import fluxo_caixa_service
from app.services.financeiro_exceptions import RegraNegocioFinanceira


def criar_conta_pagar(
    db: Session,
    *,
    id_nota: int,
    valor: float,
    data_vencimento: datetime | None = None,
    prazo_dias: int = 30,
    commit: bool = True,
) -> ContaPagar:
    nota = db.query(NotaFiscal).filter(NotaFiscal.id_nota == id_nota).first()
    if not nota:
        raise RegraNegocioFinanceira("Nota fiscal não encontrada.")
    if valor <= 0:
        raise RegraNegocioFinanceira("O valor da conta deve ser maior que zero.")
    if not isclose(float(valor), float(nota.valor_total), abs_tol=0.01):
        raise RegraNegocioFinanceira("O valor da conta deve ser igual ao total da nota fiscal.")
    if db.query(ContaPagar).filter(ContaPagar.id_nota == id_nota).first():
        raise RegraNegocioFinanceira("Já existe uma conta a pagar para esta nota fiscal.")
    if prazo_dias < 0:
        raise RegraNegocioFinanceira("O prazo de pagamento não pode ser negativo.")

    conta = ContaPagar(
        id_nota=id_nota,
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


def listar_contas_pagar(
    db: Session,
    status: str | None = None,
    somente_vencidas: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[ContaPagar]:
    query = db.query(ContaPagar)
    if status:
        query = query.filter(ContaPagar.status_pagamento == status)
    if somente_vencidas:
        query = query.filter(
            ContaPagar.status_pagamento == "pendente",
            ContaPagar.data_vencimento < fluxo_caixa_service.agora_utc(),
        )
    return query.order_by(ContaPagar.data_vencimento).offset(skip).limit(limit).all()


def buscar_conta_pagar(db: Session, id_conta_pagar: int) -> ContaPagar | None:
    return db.query(ContaPagar).filter(ContaPagar.id_conta_pagar == id_conta_pagar).first()


def atualizar_conta_pagar(
    db: Session, id_conta_pagar: int, dados: ContaPagarUpdate
) -> ContaPagar | None:
    conta = buscar_conta_pagar(db, id_conta_pagar)
    if not conta:
        return None
    if conta.status_pagamento != "pendente":
        raise RegraNegocioFinanceira("Somente contas pendentes podem ser alteradas.")

    alteracoes = dados.model_dump(exclude_unset=True)
    if "valor" in alteracoes:
        nota = db.query(NotaFiscal).filter(NotaFiscal.id_nota == conta.id_nota).first()
        if not nota or not isclose(float(alteracoes["valor"]), float(nota.valor_total), abs_tol=0.01):
            raise RegraNegocioFinanceira("O valor da conta deve ser igual ao total da nota fiscal.")
    for campo, valor in alteracoes.items():
        setattr(conta, campo, valor)
    db.commit()
    db.refresh(conta)
    return conta


def dar_baixa(db: Session, id_conta_pagar: int) -> ContaPagar | None:
    """Confirma o pagamento e grava a saída na mesma transação."""
    conta = (
        db.query(ContaPagar)
        .filter(ContaPagar.id_conta_pagar == id_conta_pagar)
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
            id_conta_pagar=conta.id_conta_pagar,
            id_conta_receber=None,
            tipo_lancamento="saida",
            valor=conta.valor,
            commit=False,
        )
        db.commit()
        db.refresh(conta)
        return conta
    except Exception:
        db.rollback()
        raise


def excluir_conta_pagar(db: Session, id_conta_pagar: int) -> bool:
    conta = buscar_conta_pagar(db, id_conta_pagar)
    if not conta:
        return False
    if conta.status_pagamento != "pendente":
        raise RegraNegocioFinanceira("Somente contas pendentes podem ser excluídas.")
    if db.query(FluxoCaixa).filter(FluxoCaixa.id_conta_pagar == id_conta_pagar).first():
        raise RegraNegocioFinanceira("A conta possui movimentação financeira e não pode ser excluída.")
    db.delete(conta)
    db.commit()
    return True
