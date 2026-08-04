from pydantic import BaseModel, ConfigDict 
from datetime import datetime

class PedidoCompraCreate(BaseModel):
    id_fornecedor: int
    status_pedido: str
    prazo_entrega_dias: int
    
class PedidoCompraOut(PedidoCompraCreate):
    id_pedido: int
    id_fornecedor: int
    data_pedido: datetime
    status_pedido: str
    prazo_entrega_dias: int
    
    model_config = ConfigDict(from_attributes=True)