from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.Vendas import VendaCreate, VendaOut
from app.services import venda_service
from app.services.financeiro_exceptions import RegraNegocioFinanceira


router = APIRouter(prefix="/vendas", tags=["Vendas"])


@router.post("/", response_model=VendaOut, status_code=status.HTTP_201_CREATED)
def criar_venda(venda: VendaCreate, db: Session = Depends(get_db)):
    try:
        return venda_service.criar_venda(db, venda)
    except RegraNegocioFinanceira as erro:
        raise HTTPException(status_code=409, detail=str(erro)) from erro


@router.get("/", response_model=list[VendaOut])
def listar_vendas(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return venda_service.listar_vendas(db, skip, limit)


@router.get("/{id_venda}", response_model=VendaOut)
def buscar_venda(id_venda: int, db: Session = Depends(get_db)):
    venda = venda_service.buscar_venda(db, id_venda)
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada.")
    return venda
