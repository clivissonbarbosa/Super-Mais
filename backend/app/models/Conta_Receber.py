from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class ContaReceber(Base):
    __tablename__ = "conta_receber"

    __table_args__ = (
        UniqueConstraint("id_venda", name="uq_conta_receber_id_venda"),
        CheckConstraint("valor > 0", name="ck_conta_receber_valor_positivo"),
        CheckConstraint(
            "status_pagamento IN ('pendente', 'pago', 'cancelado')",
            name="ck_conta_receber_status",
        ),
    )

    id_conta_receber = Column(Integer, primary_key=True)
    id_venda = Column(Integer, ForeignKey("venda.id_venda"), nullable=False)
    data_vencimento = Column(DateTime, nullable=False)
    valor = Column(Float, nullable=False)
    status_pagamento = Column(String, nullable=False, default="pendente")
