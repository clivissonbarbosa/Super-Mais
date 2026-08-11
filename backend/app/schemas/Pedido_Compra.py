from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


StatusPedido = Literal["pendente", "aprovado", "recebido", "cancelado"]


class PedidoCompraItemCreate(BaseModel):
    id_produto: int = Field(gt=0)
    quantidade: int = Field(gt=0)
    preco_unitario: float = Field(gt=0)


class PedidoCompraItemOut(PedidoCompraItemCreate):
    id_item: int
    id_pedido: int

    model_config = ConfigDict(from_attributes=True)


class PedidoCompraCreate(BaseModel):
    id_fornecedor: int = Field(gt=0)
    id_unidade: int | None = Field(default=None, gt=0)
    status_pedido: StatusPedido = "pendente"
    prazo_entrega_dias: int = Field(ge=0)
    itens: list[PedidoCompraItemCreate] = Field(default_factory=list)


class PedidoStatusUpdate(BaseModel):
    status_pedido: StatusPedido


class PedidoCompraOut(BaseModel):
    id_pedido: int
    id_fornecedor: int
    id_unidade: int | None = None
    id_usuario: int | None = None
    data_pedido: datetime
    status_pedido: StatusPedido
    prazo_entrega_dias: int
    itens: list[PedidoCompraItemOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
