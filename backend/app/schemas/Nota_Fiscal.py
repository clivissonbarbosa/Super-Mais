from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotaFiscalCreate(BaseModel):
    id_pedido: int = Field(gt=0)
    numero_nota: str = Field(min_length=1, max_length=100)
    valor_total: float = Field(gt=0)

class NotaFiscalOut(NotaFiscalCreate):
    id_nota: int 
    id_pedido: int 
    numero_nota: str
    data_emissao: datetime
    valor_total: float
    
    model_config = ConfigDict(from_attributes=True)
