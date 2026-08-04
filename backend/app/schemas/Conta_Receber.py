from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ContaReceberCreate(BaseModel):
    id_venda: int
    id_cliente: int
    data_vencimento: datetime
    valor: float
    status_pagamento: str
    
class ContaReceberOut(ContaReceberCreate):
    id_conta_receber: int
    id_venda: int
    id_cliente: int
    data_vencimento: str
    valor: float
    status_pagamento: str
    
    model_config = ConfigDict(from_attributes=True)