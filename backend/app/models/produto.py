# backend/app/models/produto.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database import Base

class Produto(Base):
    __tablename__ = "produto"
    id_produto = Column(Integer, primary_key=True)
    id_categoria = Column(Integer, ForeignKey("categoria.id_categoria"), nullable=False)
    nome = Column(String, nullable=False)
    codigo_barras = Column(String)
    preco_venda = Column(Float, nullable=False)