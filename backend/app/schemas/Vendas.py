from pydantic import BaseModel

class VendaCreate(BaseModel):
    id_unidade: int
    id_usuario: int
    id_cliente: int | None = None
    id_produto: int | None = None
    data_hora: str | None = None
    valor_total: float
    forma_pagamento: str


class VendaOut(BaseModel):
    id_venda: int
    id_unidade: int
    id_usuario: int
    id_cliente: int | None = None
    id_produto: int | None = None
    data_hora: str | None = None
    valor_total: float
    forma_pagamento: str

    class Config:
        orm_mode = True