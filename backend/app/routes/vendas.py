from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

from app.models import Vendas
from app.schemas.Vendas import VendaCreate, VendaOut

router = APIRouter(prefix="/vendas", tags=["Vendas"])

@router.post("/", response_model=VendaOut)
def criar_venda(venda: VendaCreate, db: Session = Depends(get_db)):
    nova_venda = Vendas.Venda(**venda.dict())
    db.add(nova_venda)
    db.commit()
    db.refresh(nova_venda)
    return nova_venda

@router.get("/", response_model=list[VendaOut])
def listar_vendas(db: Session = Depends(get_db)):
    return db.query(Venda).all()

