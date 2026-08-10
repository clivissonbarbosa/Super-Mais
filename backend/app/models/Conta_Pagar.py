from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class ContaPagar(Base):
    __tablename__ = "conta_pagar"

    __table_args__ = (
        UniqueConstraint("id_nota", name="uq_conta_pagar_id_nota"),
        CheckConstraint("valor > 0", name="ck_conta_pagar_valor_positivo"),
        CheckConstraint(
            "status_pagamento IN ('pendente', 'pago', 'cancelado')",
            name="ck_conta_pagar_status",
        ),
    )

    id_conta_pagar = Column(Integer, primary_key=True)
    id_nota = Column(Integer, ForeignKey("nota_fiscal.id_nota"), nullable=False)
    data_vencimento = Column(DateTime, nullable=False)
    valor = Column(Float, nullable=False)
    status_pagamento = Column(String, nullable=False, default="pendente")
