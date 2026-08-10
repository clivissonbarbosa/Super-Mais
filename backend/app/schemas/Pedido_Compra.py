from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


StatusPedido = Literal["pendente", "aprovado", "recebido", "cancelado"]


class PedidoCompraCreate(BaseModel):
    id_fornecedor: int = Field(gt=0)
    status_pedido: StatusPedido = "pendente"
    prazo_entrega_dias: int = Field(ge=0)


class PedidoStatusUpdate(BaseModel):
    status_pedido: StatusPedido
    
class PedidoCompraOut(PedidoCompraCreate):
    id_pedido: int
    id_fornecedor: int
    data_pedido: datetime
    status_pedido: StatusPedido
    prazo_entrega_dias: int
    
    model_config = ConfigDict(from_attributes=True)
