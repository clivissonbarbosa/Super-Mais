from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint

from app.database import Base


class FluxoCaixa(Base):
    __tablename__ = "fluxo_caixa"

    __table_args__ = (
        UniqueConstraint("id_conta_pagar", name="uq_fluxo_caixa_conta_pagar"),
        UniqueConstraint("id_conta_receber", name="uq_fluxo_caixa_conta_receber"),
        CheckConstraint("valor > 0", name="ck_fluxo_caixa_valor_positivo"),
        CheckConstraint(
            "(id_conta_pagar IS NOT NULL AND id_conta_receber IS NULL) OR "
            "(id_conta_pagar IS NULL AND id_conta_receber IS NOT NULL)",
            name="ck_fluxo_caixa_uma_origem",
        ),
        CheckConstraint(
            "(id_conta_pagar IS NOT NULL AND tipo_lancamento = 'saida') OR "
            "(id_conta_receber IS NOT NULL AND tipo_lancamento = 'entrada')",
            name="ck_fluxo_caixa_tipo_origem",
        ),
    )

    id_lancamento = Column(Integer, primary_key=True)
    id_conta_pagar = Column(Integer, ForeignKey("conta_pagar.id_conta_pagar"), nullable=True)
    id_conta_receber = Column(Integer, ForeignKey("conta_receber.id_conta_receber"), nullable=True)
    tipo_lancamento = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    data_confirmacao = Column(DateTime, nullable=False)
