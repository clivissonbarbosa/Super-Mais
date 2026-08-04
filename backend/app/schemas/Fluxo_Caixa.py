from pydantic import BaseModel, ConfigDict 
from datetime import datetime

class FluxoCaixaCreate(BaseModel):
    id_conta_pagar: int 
    id_conta_receber: int
    tipo_lancamento: str
    valor: float
    
class FluxoCaixaOut(FluxoCaixaCreate):
    id_lancamento: int 
    id_conta_pagar: int 
    id_conta_receber: int
    tipo_lancamento: str
    valor: float
    data_confirmacao: datetime
    
    model_config = ConfigDict(from_attributes=True)