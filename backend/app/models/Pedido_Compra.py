from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, String
from app.database import Base 

class PedidoCompra(Base):
    __tablename__ = "pedido_compra"
    id_pedido = Column(Integer, primary_key=True)
    id_fornecedor = Column(Integer, ForeignKey("fornecedor.id"))
    data_pedido = Column(DateTime)
    status_pedido = Column(String)
    prazo_entrega_dias = Column(Integer)