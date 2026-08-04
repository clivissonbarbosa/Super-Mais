from pydantic import BaseModel, ConfigDict 

class PedidoCompraCreate(BaseModel):
    id_fornecedor: int
    status_pedido: str
    prazo_entrega_dias: int
    
class PedidoCompraOut(PedidoCompraCreate):
    id_pedido: int
    id_fornecedor: int
    data_pedido: str
    status_pedido: str
    prazo_entrega_dias: int
    
    model_config = ConfigDict(from_attributes=True)