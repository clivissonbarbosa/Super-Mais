from app.models import User
from app.schemas.User import UserCreate, UserOut
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/login", response_model=UserOut)
def criar_user(user: UserCreate, db: Session = Depends(get_db)):
    novo = User(**user.dict())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@router.get("/", response_model=list[UserOut])
def listar_users(db: Session = Depends(get_db)):
    return db.query(User).all()