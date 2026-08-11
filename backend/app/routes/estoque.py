from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.User import Usuario
from app.schemas.Estoque import (
    EstoqueMinimoUpdate,
    EstoqueMovimentacaoCreate,
    EstoqueMovimentacaoOut,
    EstoqueSaldoOut,
)
from app.services import estoque_service
from app.services.financeiro_exceptions import RegraNegocioFinanceira


router = APIRouter(
    prefix="/estoque",
    tags=["Estoque"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[EstoqueSaldoOut])
@router.get("/saldos", response_model=list[EstoqueSaldoOut])
def listar_saldos(
    id_unidade: int | None = None,
    somente_abaixo_minimo: bool = False,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return estoque_service.listar_saldos(
        db,
        id_unidade=id_unidade,
        somente_abaixo_minimo=somente_abaixo_minimo,
        skip=skip,
        limit=limit,
    )


@router.get("/saldos/{id_saldo}", response_model=EstoqueSaldoOut)
def obter_saldo(id_saldo: int, db: Session = Depends(get_db)):
    saldo = estoque_service.buscar_saldo_por_id(db, id_saldo)
    if not saldo:
        raise HTTPException(status_code=404, detail="Saldo de estoque não encontrado.")
    return saldo


@router.patch("/saldos/{id_saldo}/minimo", response_model=EstoqueSaldoOut)
def alterar_estoque_minimo(
    id_saldo: int,
    dados: EstoqueMinimoUpdate,
    db: Session = Depends(get_db),
):
    saldo = estoque_service.atualizar_estoque_minimo(
        db, id_saldo, dados.estoque_minimo
    )
    if not saldo:
        raise HTTPException(status_code=404, detail="Saldo de estoque não encontrado.")
    return saldo


@router.post(
    "/movimentacoes",
    response_model=EstoqueMovimentacaoOut,
    status_code=status.HTTP_201_CREATED,
)
def movimentar_estoque(
    dados: EstoqueMovimentacaoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return estoque_service.registrar_movimentacao(
            db,
            **dados.model_dump(),
            id_usuario=current_user.id_usuario,
            referencia_tipo="ajuste_manual",
        )
    except RegraNegocioFinanceira as erro:
        raise HTTPException(status_code=409, detail=str(erro)) from erro


@router.get("/movimentacoes", response_model=list[EstoqueMovimentacaoOut])
def listar_movimentacoes(
    id_produto: int | None = None,
    id_unidade: int | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return estoque_service.listar_movimentacoes(
        db,
        id_produto=id_produto,
        id_unidade=id_unidade,
        skip=skip,
        limit=limit,
    )
