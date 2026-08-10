from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String

from app.database import Base


class PedidoCompra(Base):
    __tablename__ = "pedido_compra"

    __table_args__ = (
        CheckConstraint("prazo_entrega_dias >= 0", name="ck_pedido_compra_prazo"),
        CheckConstraint(
            "status_pedido IN ('pendente', 'aprovado', 'recebido', 'cancelado')",
            name="ck_pedido_compra_status",
        ),
    )

    id_pedido = Column(Integer, primary_key=True)
    id_fornecedor = Column(Integer, ForeignKey("fornecedor.id"), nullable=False)
    data_pedido = Column(DateTime, nullable=False)
    status_pedido = Column(String, nullable=False, default="pendente")
    prazo_entrega_dias = Column(Integer, nullable=False)
