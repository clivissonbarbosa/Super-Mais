from pydantic import BaseModel,  ConfigDict 
from datetime import datetime

class NotaFiscalCreate(BaseModel):
    id_pedido: int 
    numero_nota: str
    valor_total: float

class NotaFiscalOut(NotaFiscalCreate):
    id_nota: int 
    id_pedido: int 
    numero_nota: str
    data_emissao: datetime
    valor_total: float
    
    model_config = ConfigDict(from_attributes=True)