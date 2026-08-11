from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True, unique=True, index=True)
    id_unidade = Column(Integer, ForeignKey("unidade.id_unidade"))
    nome = Column(String, unique=True, index=True)
    login = Column(String, unique=True, index=True)
    senha_hash = Column(String, nullable=False)
    google_id = Column(String, unique=True, index=True, nullable=True)
    foto_url = Column(String, nullable=True)
    ativo = Column(Boolean, nullable=False, default=True, server_default="true")
