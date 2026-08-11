from pydantic import BaseModel, ConfigDict, Field


class ClienteCreate(BaseModel):
    cpf: str = Field(min_length=11, max_length=14)
    nome: str = Field(min_length=1, max_length=160)
    segmento_marketing: str | None = Field(default=None, max_length=120)


class ClienteOut(ClienteCreate):
    id_cliente: int

    model_config = ConfigDict(from_attributes=True)
