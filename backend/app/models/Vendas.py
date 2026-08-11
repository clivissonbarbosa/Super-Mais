# backend/app/models/vendas.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class Venda(Base):
    __tablename__ = "venda"
    id_venda = Column(Integer, primary_key=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"))
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"))
    id_cliente = Column(Integer, ForeignKey("cliente.id_cliente"), nullable=True)
    id_produto = Column(Integer, ForeignKey("produto.id_produto"), nullable=True)
    data_hora = Column(DateTime, server_default=func.now())
    valor_total = Column(Float)
    forma_pagamento = Column(String)

    itens = relationship(
        "VendaItem",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
