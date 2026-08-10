from sqlalchemy.orm import Session

from app.models.Fornecedor import Fornecedor
from app.models.Pedido_Compra import PedidoCompra
from app.schemas.Pedido_Compra import PedidoCompraCreate
from app.services import fluxo_caixa_service
from app.services.financeiro_exceptions import RegraNegocioFinanceira


STATUS_PEDIDO = {"pendente", "aprovado", "recebido", "cancelado"}


def criar_pedido_compra(db: Session, pedido: PedidoCompraCreate) -> PedidoCompra:
    if pedido.status_pedido not in STATUS_PEDIDO:
        raise RegraNegocioFinanceira("Status de pedido inválido.")
    if not db.query(Fornecedor).filter(Fornecedor.id == pedido.id_fornecedor).first():
        raise RegraNegocioFinanceira("Fornecedor não encontrado.")

    db_pedido = PedidoCompra(
        id_fornecedor=pedido.id_fornecedor,
        data_pedido=fluxo_caixa_service.agora_utc(),
        status_pedido=pedido.status_pedido,
        prazo_entrega_dias=pedido.prazo_entrega_dias,
    )
    db.add(db_pedido)
    db.commit()
    db.refresh(db_pedido)
    return db_pedido


def atualizar_status(db: Session, id_pedido: int, novo_status: str) -> PedidoCompra | None:
    if novo_status not in STATUS_PEDIDO:
        raise RegraNegocioFinanceira("Status de pedido inválido.")
    pedido = db.query(PedidoCompra).filter(PedidoCompra.id_pedido == id_pedido).first()
    if pedido:
        pedido.status_pedido = novo_status
        db.commit()
        db.refresh(pedido)
    return pedido


def listar_pedidos(db: Session, skip: int = 0, limit: int = 100) -> list[PedidoCompra]:
    return (
        db.query(PedidoCompra)
        .order_by(PedidoCompra.data_pedido.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
