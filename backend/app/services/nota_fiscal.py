from sqlalchemy.orm import Session

from app.models.Nota_Fiscal import NotaFiscal
from app.models.Pedido_Compra import PedidoCompra
from app.schemas.Nota_Fiscal import NotaFiscalCreate
from app.services import conta_pagar, fluxo_caixa_service
from app.services.financeiro_exceptions import RegraNegocioFinanceira


PRAZO_PADRAO_PAGAMENTO_DIAS = 30


def criar_nota_fiscal(db: Session, nota: NotaFiscalCreate) -> NotaFiscal:
    """Emite a nota e gera a obrigação a pagar em uma única transação."""
    pedido = db.query(PedidoCompra).filter(PedidoCompra.id_pedido == nota.id_pedido).first()
    if not pedido:
        raise RegraNegocioFinanceira("Pedido de compra não encontrado.")
    numero_nota = nota.numero_nota.strip()
    if db.query(NotaFiscal).filter(NotaFiscal.numero_nota == numero_nota).first():
        raise RegraNegocioFinanceira("Já existe uma nota fiscal com este número.")

    try:
        db_nota = NotaFiscal(
            id_pedido=nota.id_pedido,
            numero_nota=numero_nota,
            data_emissao=fluxo_caixa_service.agora_utc(),
            valor_total=nota.valor_total,
        )
        db.add(db_nota)
        db.flush()
        conta_pagar.criar_conta_pagar(
            db,
            id_nota=db_nota.id_nota,
            valor=db_nota.valor_total,
            prazo_dias=PRAZO_PADRAO_PAGAMENTO_DIAS,
            commit=False,
        )
        db.commit()
        db.refresh(db_nota)
        return db_nota
    except Exception:
        db.rollback()
        raise


def listar_notas(db: Session, skip: int = 0, limit: int = 100) -> list[NotaFiscal]:
    return (
        db.query(NotaFiscal)
        .order_by(NotaFiscal.data_emissao.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
