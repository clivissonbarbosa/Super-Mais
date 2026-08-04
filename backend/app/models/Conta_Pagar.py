from sqlalchemy import Column, DateTime, Float, Integer, ForeignKey, String
from app.database import Base 

class ContaPagar(Base):
    __tablename__ = "conta_pagar"
    id_conta_pagar = Column(Integer, primary_key=True)
    id_nota = Column(Integer, ForeignKey("nota_fiscal.id_nota"))
    data_vencimento = Column(DateTime)
    valor = Column(Float)
    status_pagamento = Column(String)