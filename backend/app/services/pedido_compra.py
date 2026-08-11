from sqlalchemy.orm import Session, selectinload

from app.models.Fornecedor import Fornecedor
from app.models.Pedido_Compra import PedidoCompra
from app.models.Pedido_Compra_Item import PedidoCompraItem
from app.models.Unidade import Unidade
from app.models.produto import Produto
from app.schemas.Pedido_Compra import PedidoCompraCreate
from app.services import fluxo_caixa_service
from app.services.financeiro_exceptions import RegraNegocioFinanceira


STATUS_PEDIDO = {"pendente", "aprovado", "recebido", "cancelado"}


def criar_pedido_compra(
    db: Session,
    pedido: PedidoCompraCreate,
    *,
    id_usuario: int | None = None,
) -> PedidoCompra:
    if pedido.status_pedido not in {"pendente", "aprovado"}:
        raise RegraNegocioFinanceira(
            "O pedido deve ser criado como pendente ou aprovado."
        )
    if not db.query(Fornecedor).filter(Fornecedor.id == pedido.id_fornecedor).first():
        raise RegraNegocioFinanceira("Fornecedor não encontrado.")
    if pedido.id_unidade is not None and not db.query(Unidade).filter(
        Unidade.id_unidade == pedido.id_unidade
    ).first():
        raise RegraNegocioFinanceira("Unidade não encontrada.")

    produtos_informados = [item.id_produto for item in pedido.itens]
    if len(produtos_informados) != len(set(produtos_informados)):
        raise RegraNegocioFinanceira("O mesmo produto não pode aparecer duas vezes no pedido.")
    if produtos_informados:
        produtos_existentes = {
            produto_id
            for (produto_id,) in db.query(Produto.id_produto)
            .filter(Produto.id_produto.in_(produtos_informados))
            .all()
        }
        faltantes = sorted(set(produtos_informados) - produtos_existentes)
        if faltantes:
            raise RegraNegocioFinanceira(
                f"Produtos não encontrados no pedido: {', '.join(map(str, faltantes))}."
            )

    try:
        db_pedido = PedidoCompra(
            id_fornecedor=pedido.id_fornecedor,
            id_unidade=pedido.id_unidade,
            id_usuario=id_usuario,
            data_pedido=fluxo_caixa_service.agora_utc(),
            status_pedido=pedido.status_pedido,
            prazo_entrega_dias=pedido.prazo_entrega_dias,
        )
        db.add(db_pedido)
        db.flush()
        for item in pedido.itens:
            db.add(
                PedidoCompraItem(
                    id_pedido=db_pedido.id_pedido,
                    id_produto=item.id_produto,
                    quantidade=item.quantidade,
                    preco_unitario=item.preco_unitario,
                )
            )
        db.commit()
        return buscar_pedido(db, db_pedido.id_pedido)
    except Exception:
        db.rollback()
        raise


def buscar_pedido(db: Session, id_pedido: int) -> PedidoCompra | None:
    return (
        db.query(PedidoCompra)
        .options(selectinload(PedidoCompra.itens))
        .filter(PedidoCompra.id_pedido == id_pedido)
        .first()
    )


def atualizar_status(
    db: Session, id_pedido: int, novo_status: str
) -> PedidoCompra | None:
    if novo_status not in STATUS_PEDIDO:
        raise RegraNegocioFinanceira("Status de pedido inválido.")
    pedido = buscar_pedido(db, id_pedido)
    if not pedido:
        return None
    if pedido.status_pedido in {"recebido", "cancelado"}:
        raise RegraNegocioFinanceira("Um pedido finalizado não pode mudar de status.")
    if novo_status == "recebido":
        raise RegraNegocioFinanceira(
            "O recebimento deve ser confirmado pela emissão da nota fiscal."
        )
    pedido.status_pedido = novo_status
    db.commit()
    db.refresh(pedido)
    return pedido


def listar_pedidos(
    db: Session, skip: int = 0, limit: int = 100
) -> list[PedidoCompra]:
    return (
        db.query(PedidoCompra)
        .options(selectinload(PedidoCompra.itens))
        .order_by(PedidoCompra.data_pedido.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
