# backend/app/routers/user.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
#from passlib.context import CryptContext
from app.database import get_db
from app.models.User import Usuario
from app.schemas.User import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["Usuarios"])
##pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/", response_model=UserOut)
def criar_usuario(usuario: UserCreate, db: Session = Depends(get_db)):
    novo = Usuario(
        id_unidade=usuario.id_unidade,
        nome=usuario.nome,
        login=usuario.login,
        # senha_hash=pwd_context.hash(usuario.senha)
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@router.get("/", response_model=list[UserOut])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).all()