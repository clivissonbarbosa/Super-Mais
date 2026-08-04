from sqlalchemy import Column, Integer, ForeignKey, String, Float, DateTime
from app.database import Base

class ContaReceber(Base):
    __tablename__ = "conta_receber"
    id_conta_receber = Column(Integer, primary_key=True)
    id_venda = Column(Integer, ForeignKey("venda.id_venda"))
    data_vencimento = Column(DateTime)
    valor = Column(Float)
    status_pagamento = Column(String)