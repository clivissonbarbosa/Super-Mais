from pydantic import BaseModel, ConfigDict, Field

class VendaItemCreate(BaseModel):
    id_venda: int = Field(gt=0)
    id_produto: int = Field(gt=0)
    quantidade: int = Field(gt=0)
    preco_unitario: float = Field(gt=0)
    
class VendaItemOut(BaseModel):
    id_item: int 
    id_venda: int 
    id_produto: int
    quantidade: int
    preco_unitario: float
    
    model_config = ConfigDict(from_attributes=True)


# Compatibilidade temporária com chamadas existentes que usavam o nome incorreto.
vendaItemCreate = VendaItemCreate
