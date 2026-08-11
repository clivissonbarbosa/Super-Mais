from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Integer, UniqueConstraint

from app.database import Base


class PedidoCompraItem(Base):
    __tablename__ = "pedido_compra_item"
    __table_args__ = (
        UniqueConstraint(
            "id_pedido", "id_produto", name="uq_pedido_compra_item_produto"
        ),
        CheckConstraint("quantidade > 0", name="ck_pedido_compra_item_quantidade"),
        CheckConstraint(
            "preco_unitario > 0", name="ck_pedido_compra_item_preco_unitario"
        ),
    )

    id_item = Column(Integer, primary_key=True)
    id_pedido = Column(
        Integer, ForeignKey("pedido_compra.id_pedido"), nullable=False, index=True
    )
    id_produto = Column(
        Integer, ForeignKey("produto.id_produto"), nullable=False, index=True
    )
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
