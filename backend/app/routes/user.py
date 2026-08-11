import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from app.core.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from app.database import get_db
from app.models.Unidade import Unidade
from app.models.User import Usuario
from app.schemas.User import GoogleTokenLogin, Token, UserCreate, UserOut


router = APIRouter(prefix="/users", tags=["Usuários"])


def _resolver_unidade(
    db: Session,
    id_unidade: int | None,
    *,
    permitir_existente_padrao: bool,
) -> Unidade:
    if id_unidade is not None:
        unidade = db.query(Unidade).filter(Unidade.id_unidade == id_unidade).first()
        if not unidade:
            raise HTTPException(status_code=404, detail="Unidade não encontrada.")
        return unidade

    unidade = db.query(Unidade).order_by(Unidade.id_unidade).first()
    if unidade and (permitir_existente_padrao or db.query(Usuario).count() == 0):
        return unidade
    if db.query(Usuario).count() == 0:
        unidade = Unidade(nome="Unidade principal", tipo="Loja")
        db.add(unidade)
        db.flush()
        return unidade
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Informe a unidade do usuário.",
    )


def _emitir_token(usuario: Usuario) -> dict[str, str]:
    token = create_access_token({"sub": str(usuario.id_usuario)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def criar_usuario(usuario: UserCreate, db: Session = Depends(get_db)):
    login = usuario.login.strip().lower()
    nome = usuario.nome.strip()
    if db.query(Usuario).filter(Usuario.login == login).first():
        raise HTTPException(status_code=409, detail="Login já cadastrado.")
    if db.query(Usuario).filter(Usuario.nome == nome).first():
        raise HTTPException(status_code=409, detail="Nome já cadastrado.")

    unidade = _resolver_unidade(
        db, usuario.id_unidade, permitir_existente_padrao=False
    )
    novo = Usuario(
        id_unidade=unidade.id_unidade,
        nome=nome,
        login=login,
        senha_hash=get_password_hash(usuario.senha),
        ativo=True,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.get("/", response_model=list[UserOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return db.query(Usuario).order_by(Usuario.nome).all()


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    usuario = authenticate_user(db, form_data.username.strip().lower(), form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _emitir_token(usuario)


@router.post("/google", response_model=Token)
def login_google(dados: GoogleTokenLogin, db: Session = Depends(get_db)):
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login Google ainda não foi configurado na API.",
        )
    try:
        claims = google_id_token.verify_oauth2_token(
            dados.id_token,
            google_requests.Request(),
            client_id,
        )
    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Google inválido.",
        ) from erro

    if not claims.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="O e-mail da conta Google não foi verificado.",
        )
    google_id = claims.get("sub")
    email = str(claims.get("email", "")).strip().lower()
    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A conta Google não retornou identificação suficiente.",
        )

    usuario = db.query(Usuario).filter(Usuario.google_id == google_id).first()
    if not usuario:
        usuario = db.query(Usuario).filter(Usuario.login == email).first()
    if usuario:
        if usuario.ativo is False:
            raise HTTPException(status_code=403, detail="Usuário inativo.")
        if usuario.google_id not in {None, google_id}:
            raise HTTPException(
                status_code=409,
                detail="O e-mail já está vinculado a outra conta Google.",
            )
        usuario.google_id = google_id
        usuario.foto_url = claims.get("picture")
        db.commit()
        db.refresh(usuario)
        return _emitir_token(usuario)

    unidade = _resolver_unidade(
        db, dados.id_unidade, permitir_existente_padrao=True
    )
    nome = str(claims.get("name") or email).strip()
    if db.query(Usuario).filter(Usuario.nome == nome).first():
        nome = f"{nome} ({email})"
    usuario = Usuario(
        id_unidade=unidade.id_unidade,
        nome=nome,
        login=email,
        senha_hash=get_password_hash(secrets.token_urlsafe(32)),
        google_id=google_id,
        foto_url=claims.get("picture"),
        ativo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return _emitir_token(usuario)


@router.get("/me", response_model=UserOut)
def ler_usuario_logado(current_user: Usuario = Depends(get_current_user)):
    return current_user
