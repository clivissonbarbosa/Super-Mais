from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, String
from app.database import Base 

class NotaFiscal(Base):
    __tablename__ = "nota_fiscal"
    id_nota = Column(Integer, primary_key=True)
    id_pedido = Column(Integer, ForeignKey("pedido_compra.id_pedido"))
    numero_nota = Column(String)
    data_emissao = Column(DateTime)
    valor_total = Column(Float)
    