from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ContaPagarCreate(BaseModel):
    id_nota: int 
    id_cliente: int 
    valor: float 
    status_pagamento: str

class ContaPagarOut(ContaPagarCreate):
    id_conta_pagar: int 
    id_nota: int 
    data_vencimento: datetime 
    valor: float 
    status_pagamento: str

    model_config = ConfigDict(from_attributes=True)