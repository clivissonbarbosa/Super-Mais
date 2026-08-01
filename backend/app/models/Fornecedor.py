## Fornedora model
from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class Fornecedor(Base):
    __tablename__ = "fornecedor"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True)
    cnpj = Column(String, unique=True, index=True)
    endereco = Column(String)
    telefone = Column(String)