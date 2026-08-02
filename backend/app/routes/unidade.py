# backend/app/routers/unidade.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.Unidade import Unidade
from app.schemas.Unidade import UnidadeCreate, UnidadeOut

router = APIRouter(prefix="/unidades", tags=["Unidades"])

@router.post("/", response_model=UnidadeOut)
def criar_unidade(unidade: UnidadeCreate, db: Session = Depends(get_db)):
    nova = Unidade(**unidade.dict())
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova

@router.get("/", response_model=list[UnidadeOut])
def listar_unidades(db: Session = Depends(get_db)):
    return db.query(Unidade).all()