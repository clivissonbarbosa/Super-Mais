from sqlalchemy import Column, Integer, ForeignKey, Float 
from app.database import Base 

class VendaItem(Base):
    __tablename__ = "venda_item"
    id_item = Column(Integer, primary_key=True)
    id_venda = Column(Integer, ForeignKey("venda.id_venda"))
    id_produto = Column(Integer, ForeignKey("produto.id_produto"))
    quantidade = Column(Integer)
    preco_unitario = Column(Float)