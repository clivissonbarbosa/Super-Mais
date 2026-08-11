from pydantic import BaseModel, ConfigDict, Field, field_validator


class FornecedorCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    cnpj: str = Field(min_length=14, max_length=18)
    endereco: str = Field(min_length=3, max_length=255)
    telefone: str = Field(min_length=8, max_length=20)

    @field_validator("nome", "cnpj", "endereco", "telefone")
    @classmethod
    def remover_espacos(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("O campo não pode ficar vazio.")
        return valor


class FornecedorOut(FornecedorCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
