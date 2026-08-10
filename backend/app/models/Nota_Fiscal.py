from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String

from app.database import Base


class NotaFiscal(Base):
    __tablename__ = "nota_fiscal"

    __table_args__ = (
        CheckConstraint("valor_total > 0", name="ck_nota_fiscal_valor_positivo"),
    )

    id_nota = Column(Integer, primary_key=True)
    id_pedido = Column(Integer, ForeignKey("pedido_compra.id_pedido"), nullable=False)
    numero_nota = Column(String, nullable=False, unique=True)
    data_emissao = Column(DateTime, nullable=False)
    valor_total = Column(Float, nullable=False)
