from pydantic import BaseModel, ConfigDict

class vendaItemCreate(BaseModel):
    id_venda: int
    id_produto: int 
    quantidade: int 
    preco_unitario: float
    
class VendaItemOut(BaseModel):
    id_item: int 
    id_venda: int 
    quantidade: int
    preco_unitario: float
    
    model_config = ConfigDict(from_attributes=True)