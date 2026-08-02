# backend/app/models/unidade.py
from sqlalchemy import Column, Integer, String
from app.database import Base

class Unidade(Base):
    __tablename__ = "unidade"
    id_unidade = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    tipo = Column(String, nullable=False)  # "Loja" ou "CD"