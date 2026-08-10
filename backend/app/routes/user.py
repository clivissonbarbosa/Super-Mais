# backend/app/routers/user.py
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import (
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
)
from app.database import get_db
from app.models.User import Usuario
from app.schemas.User import Token, UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def criar_usuario(usuario: UserCreate, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.login == usuario.login).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login já cadastrado",
        )

    if db.query(Usuario).filter(Usuario.nome == usuario.nome).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome já cadastrado",
        )

    novo = Usuario(
        id_unidade=usuario.id_unidade,
        nome=usuario.nome,
        login=usuario.login,
        senha_hash=get_password_hash(usuario.senha),
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
    return db.query(Usuario).all()


@router.post("/login", response_model=Token)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    usuario = authenticate_user(db, form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(usuario.id_usuario)})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def ler_usuario_logado(current_user: Usuario = Depends(get_current_user)):
    return current_user