# backend/app/routers/user.py
import os
from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv
from fastapi import HTTPException,status,APIRouter, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database import get_db
from app.models.User import Usuario
from app.schemas.User import UserCreate, UserOut
from fastapi.security import OAuth2PasswordRequestForm

load_dotenv()

router = APIRouter(prefix="/users", tags=["Usuarios"])

##pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def criarToken(dados:dict):
    data = dados.copy()
    expire = datetime.timezone.utc() + timedelta(minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    data.update({"exp": expire})
    token = jwt.encode(data, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))
    return token

@router.post("/", response_model=UserOut)
def criar_usuario(usuario: UserCreate, db: Session = Depends(get_db)):
    novo = Usuario(
        id_unidade=usuario.id_unidade,
        nome=usuario.nome,
        login=usuario.login,
        senha_hash=usuario.senha
        #senha_hash=pwd_context.hash(usuario.senha)
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@router.get("/", response_model=list[UserOut])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).all()

@router.post("/login")
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    usuario = db.query(Usuario).filter(Usuario.login == form_data.username).first()
    if not usuario or usuario.senha_hash != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )
    token = criarToken({"sub": str(usuario.id_usuario)})
    return {"access_token": token, "token_type": "bearer"}