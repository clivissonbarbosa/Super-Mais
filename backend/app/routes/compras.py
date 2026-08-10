from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.Nota_Fiscal import NotaFiscalCreate, NotaFiscalOut
from app.schemas.Pedido_Compra import PedidoCompraCreate, PedidoCompraOut, PedidoStatusUpdate
from app.services import nota_fiscal, pedido_compra
from app.services.financeiro_exceptions import RegraNegocioFinanceira
from backend.app.core.security import get_current_user


router = APIRouter(prefix="/compras", tags=["Compras"], dependencies=[Depends(get_current_user)])


def _conflito(erro: RegraNegocioFinanceira) -> HTTPException:
    return HTTPException(status_code=409, detail=str(erro))


@router.post("/pedidos", response_model=PedidoCompraOut, status_code=status.HTTP_201_CREATED)
def criar_pedido(dados: PedidoCompraCreate, db: Session = Depends(get_db)):
    try:
        return pedido_compra.criar_pedido_compra(db, dados)
    except RegraNegocioFinanceira as erro:
        raise _conflito(erro) from erro


@router.get("/pedidos", response_model=list[PedidoCompraOut])
def listar_pedidos(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return pedido_compra.listar_pedidos(db, skip, limit)


@router.patch("/pedidos/{id_pedido}/status", response_model=PedidoCompraOut)
def atualizar_status_pedido(
    id_pedido: int, dados: PedidoStatusUpdate, db: Session = Depends(get_db)
):
    try:
        pedido = pedido_compra.atualizar_status(db, id_pedido, dados.status_pedido)
    except RegraNegocioFinanceira as erro:
        raise _conflito(erro) from erro
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido de compra não encontrado.")
    return pedido


@router.post("/notas-fiscais", response_model=NotaFiscalOut, status_code=status.HTTP_201_CREATED)
def emitir_nota_fiscal(dados: NotaFiscalCreate, db: Session = Depends(get_db)):
    try:
        return nota_fiscal.criar_nota_fiscal(db, dados)
    except RegraNegocioFinanceira as erro:
        raise _conflito(erro) from erro


@router.get("/notas-fiscais", response_model=list[NotaFiscalOut])
def listar_notas_fiscais(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return nota_fiscal.listar_notas(db, skip, limit)
