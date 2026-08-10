from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Integer

from app.database import Base


class VendaItem(Base):
    __tablename__ = "venda_item"

    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_venda_item_quantidade_positiva"),
        CheckConstraint("preco_unitario > 0", name="ck_venda_item_preco_positivo"),
    )

    id_item = Column(Integer, primary_key=True)
    id_venda = Column(Integer, ForeignKey("venda.id_venda"), nullable=False)
    id_produto = Column(Integer, ForeignKey("produto.id_produto"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
