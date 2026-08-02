from app.database import Base
from sqlalchemy import Column, Integer, String, Float


class Categoria(Base):
    __tablename__ = "categoria"
    id_categoria = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False) 
    margem_lucro = Column(Float, nullable=True)