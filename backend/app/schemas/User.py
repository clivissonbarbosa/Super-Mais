from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    id_unidade: int | None = None
    nome: str
    login: str


class UserCreate(BaseModel):
    id_unidade: int | None = None
    nome: str = Field(min_length=1, max_length=160)
    login: str = Field(min_length=1, max_length=160)
    senha: str = Field(min_length=6, max_length=128)


class UserOut(UserBase):
    id_usuario: int
    google_id: str | None = None
    foto_url: str | None = None
    ativo: bool = True

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class GoogleTokenLogin(BaseModel):
    id_token: str = Field(min_length=20)
    id_unidade: int | None = Field(default=None, gt=0)


class TokenData(BaseModel):
    sub: str | None = None
