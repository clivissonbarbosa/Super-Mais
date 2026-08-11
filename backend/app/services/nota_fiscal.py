from sqlalchemy.orm import Session, selectinload

from app.models.Nota_Fiscal import NotaFiscal
from app.models.Pedido_Compra import PedidoCompra
from app.schemas.Nota_Fiscal import NotaFiscalCreate
from app.services import conta_pagar, estoque_service, fluxo_caixa_service
from app.services.financeiro_exceptions import RegraNegocioFinanceira


PRAZO_PADRAO_PAGAMENTO_DIAS = 30


def criar_nota_fiscal(
    db: Session,
    nota: NotaFiscalCreate,
    *,
    id_usuario: int | None = None,
) -> NotaFiscal:
    """Recebe o pedido, movimenta estoque e gera a conta a pagar atomicamente."""
    pedido = (
        db.query(PedidoCompra)
        .options(selectinload(PedidoCompra.itens))
        .filter(PedidoCompra.id_pedido == nota.id_pedido)
        .first()
    )
    if not pedido:
        raise RegraNegocioFinanceira("Pedido de compra não encontrado.")
    if pedido.status_pedido == "cancelado":
        raise RegraNegocioFinanceira("Não é possível receber um pedido cancelado.")
    if pedido.status_pedido == "recebido":
        raise RegraNegocioFinanceira("Este pedido já foi recebido.")
    if db.query(NotaFiscal).filter(NotaFiscal.id_pedido == nota.id_pedido).first():
        raise RegraNegocioFinanceira("Este pedido já possui nota fiscal.")

    numero_nota = nota.numero_nota.strip()
    if db.query(NotaFiscal).filter(NotaFiscal.numero_nota == numero_nota).first():
        raise RegraNegocioFinanceira("Já existe uma nota fiscal com este número.")

    itens = list(pedido.itens)
    total_itens = round(
        sum(item.quantidade * item.preco_unitario for item in itens), 2
    )
    if itens and pedido.id_unidade is None:
        raise RegraNegocioFinanceira(
            "O pedido precisa informar a unidade para gerar a entrada no estoque."
        )
    if itens and nota.valor_total is not None and abs(nota.valor_total - total_itens) > 0.01:
        raise RegraNegocioFinanceira(
            f"O valor da nota deve coincidir com o total dos itens: {total_itens:.2f}."
        )
    valor_total = total_itens if itens else nota.valor_total
    if valor_total is None or valor_total <= 0:
        raise RegraNegocioFinanceira(
            "Informe itens no pedido ou o valor total da nota fiscal."
        )

    try:
        db_nota = NotaFiscal(
            id_pedido=nota.id_pedido,
            numero_nota=numero_nota,
            data_emissao=fluxo_caixa_service.agora_utc(),
            valor_total=valor_total,
        )
        db.add(db_nota)
        db.flush()

        for item in itens:
            estoque_service.registrar_movimentacao(
                db,
                id_produto=item.id_produto,
                id_unidade=pedido.id_unidade,
                tipo_movimento="entrada",
                quantidade=item.quantidade,
                motivo=f"Recebimento do pedido #{pedido.id_pedido}",
                id_usuario=id_usuario,
                referencia_tipo="nota_fiscal",
                referencia_id=db_nota.id_nota,
                commit=False,
            )

        conta_pagar.criar_conta_pagar(
            db,
            id_nota=db_nota.id_nota,
            valor=db_nota.valor_total,
            prazo_dias=PRAZO_PADRAO_PAGAMENTO_DIAS,
            commit=False,
        )
        pedido.status_pedido = "recebido"
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
