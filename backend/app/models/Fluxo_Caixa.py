from sqlalchemy import Column, DateTime, Integer, ForeignKey, String, Float
from app.database import Base

class FluxoCaixa(Base):
    __tablename__ = "fluxo_caixa"
    id_lancamento = Column(Integer, primary_key=True)
    id_conta_pagar = Column(Integer, ForeignKey("conta_pagar.id_conta_pagar"))
    id_conta_receber = Column(Integer, ForeignKey("conta_receber.id_conta_receber"))
    tipo_lancamento = Column(String)  # Débito ou Crédito
    valor = Column(Float)
    data_confirmacao = Column(DateTime)