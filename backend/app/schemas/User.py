from pydantic import BaseModel

class UserBase(BaseModel):
    id_unidade: int
    nome: str
    login: str


class UserCreate(BaseModel):
    id_unidade: int
    nome: str
    login: str
    senha: str


class UserOut(UserBase):
    id_usuario: int
    ativo: bool = True

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    sub: str | None = None