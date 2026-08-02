from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True, unique=True, index=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"))
    nome = Column(String, unique=True, index=True)
    login = Column(String, unique=True, index=True)
    senha_hash = Column(String, nullable=False)
    balance = Column(Float, default=0.0)