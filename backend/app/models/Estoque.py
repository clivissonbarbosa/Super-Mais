# backend/app/models/estoque.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class EstoqueSaldo(Base):
    __tablename__ = "estoque_saldo"
    id_saldo = Column(Integer, primary_key=True)
    id_produto = Column(Integer, ForeignKey("produto.id_produto"))
   ## id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"))
    quantidade_atual = Column(Integer, nullable=False, default=0)
    estoque_minimo = Column(Integer, nullable=False, default=0)

    produto = relationship("Produto")
    ## unidade = relationship("Unidade")


class EstoqueMovimentacao(Base):
    __tablename__ = "estoque_movimentacao"
    id_movimentacao = Column(Integer, primary_key=True)
    id_produto = Column(Integer, ForeignKey("produto.id_produto"))
    ## id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"))
    tipo_movimento = Column(String)   # Entrada, Saída, Perda
    quantidade = Column(Integer)
    data_movimentacao = Column(DateTime, server_default=func.now())
    motivo = Column(String)           # Vencimento, Venda, Inventário