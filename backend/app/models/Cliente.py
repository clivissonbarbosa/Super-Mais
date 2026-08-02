# backend/app/models/Cliente.py
from sqlalchemy import Column, Integer, String
from app.database import Base

class Cliente(Base):
    __tablename__ = "cliente"
    id_cliente = Column(Integer, primary_key=True)
    cpf = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)
    segmento_marketing = Column(String, nullable=True)