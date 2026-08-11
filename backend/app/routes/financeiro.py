from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.Conta_Pagar import ContaPagarCreate, ContaPagarOut, ContaPagarUpdate
from app.schemas.Conta_Receber import ContaReceberCreate, ContaReceberOut, ContaReceberUpdate
from app.schemas.Fluxo_Caixa import FluxoCaixaOut, ResumoFinanceiroOut
from app.services import conta_pagar, conta_receber, fluxo_caixa_service
from app.services.financeiro_exceptions import RegraNegocioFinanceira
from app.core.security import get_current_user
from app.models.User import Usuario


router = APIRouter(prefix="/financeiro", tags=["Financeiro"], dependencies=[Depends(get_current_user)])
StatusPagamento = Literal["pendente", "pago", "cancelado"]


def _conflito_regra_negocio(erro: RegraNegocioFinanceira) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))


@router.post(
    "/contas-pagar",
    response_model=ContaPagarOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_conta_pagar(dados: ContaPagarCreate, db: Session = Depends(get_db)):
    try:
        return conta_pagar.criar_conta_pagar(
            db,
            id_nota=dados.id_nota,
            data_vencimento=dados.data_vencimento,
            valor=dados.valor,
        )
    except RegraNegocioFinanceira as erro:
        raise _conflito_regra_negocio(erro) from erro


@router.get("/contas-pagar", response_model=list[ContaPagarOut])
def listar_contas_pagar(
    status_pagamento: StatusPagamento | None = None,
    somente_vencidas: bool = False,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return conta_pagar.listar_contas_pagar(
        db, status_pagamento, somente_vencidas, skip, limit
    )


@router.get("/contas-pagar/{id_conta}", response_model=ContaPagarOut)
def buscar_conta_pagar(id_conta: int, db: Session = Depends(get_db)):
    conta = conta_pagar.buscar_conta_pagar(db, id_conta)
    if not conta:
        raise HTTPException(status_code=404, detail="Conta a pagar não encontrada.")
    return conta


@router.patch("/contas-pagar/{id_conta}", response_model=ContaPagarOut)
def atualizar_conta_pagar(
    id_conta: int, dados: ContaPagarUpdate, db: Session = Depends(get_db)
):
    try:
        conta = conta_pagar.atualizar_conta_pagar(db, id_conta, dados)
    except RegraNegocioFinanceira as erro:
        raise _conflito_regra_negocio(erro) from erro
    if not conta:
        raise HTTPException(status_code=404, detail="Conta a pagar não encontrada.")
    return conta


@router.post("/contas-pagar/{id_conta}/baixa", response_model=ContaPagarOut)
def baixar_conta_pagar(
    id_conta: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        conta = conta_pagar.dar_baixa(
            db, id_conta, id_usuario=current_user.id_usuario
        )
    except RegraNegocioFinanceira as erro:
        raise _conflito_regra_negocio(erro) from erro
    if not conta:
        raise HTTPException(status_code=404, detail="Conta a pagar não encontrada.")
    return conta


@router.delete("/contas-pagar/{id_conta}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_conta_pagar(id_conta: int, db: Session = Depends(get_db)):
    try:
        removida = conta_pagar.excluir_conta_pagar(db, id_conta)
    except RegraNegocioFinanceira as erro:
        raise _conflito_regra_negocio(erro) from erro
    if not removida:
        raise HTTPException(status_code=404, detail="Conta a pagar não encontrada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/contas-receber",
    response_model=ContaReceberOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_conta_receber(dados: ContaReceberCreate, db: Session = Depends(get_db)):
    try:
        return conta_receber.criar_conta_receber(
            db,
            id_venda=dados.id_venda,
            data_vencimento=dados.data_vencimento,
            valor=dados.valor,
        )
    except RegraNegocioFinanceira as erro:
        raise _conflito_regra_negocio(erro) from erro


@router.get("/contas-receber", response_model=list[ContaReceberOut])
def listar_contas_receber(
    status_pagamento: StatusPagamento | None = None,
    somente_vencidas: bool = False,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return conta_receber.listar_contas_receber(
        db, status_pagamento, somente_vencidas, skip, limit
    )


@router.get("/contas-receber/{id_conta}", response_model=ContaReceberOut)
def buscar_conta_receber(id_conta: int, db: Session = Depends(get_db)):
    conta = conta_receber.buscar_conta_receber(db, id_conta)
    if not conta:
        raise HTTPException(status_code=404, detail="Conta a receber não encontrada.")
    return conta


@router.patch("/contas-receber/{id_conta}", response_model=ContaReceberOut)
def atualizar_conta_receber(
    id_conta: int, dados: ContaReceberUpdate, db: Session = Depends(get_db)
):
    try:
        conta = conta_receber.atualizar_conta_receber(db, id_conta, dados)
    except RegraNegocioFinanceira as erro:
        raise _conflito_regra_negocio(erro) from erro
    if not conta:
        raise HTTPException(status_code=404, detail="Conta a receber não encontrada.")
    return conta


@router.post("/contas-receber/{id_conta}/baixa", response_model=ContaReceberOut)
def baixar_conta_receber(
    id_conta: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        conta = conta_receber.dar_baixa(
            db, id_conta, id_usuario=current_user.id_usuario
        )
    except RegraNegocioFinanceira as erro:
        raise _conflito_regra_negocio(erro) from erro
    if not conta:
        raise HTTPException(status_code=404, detail="Conta a receber não encontrada.")
    return conta


@router.delete("/contas-receber/{id_conta}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_conta_receber(id_conta: int, db: Session = Depends(get_db)):
    try:
        removida = conta_receber.excluir_conta_receber(db, id_conta)
    except RegraNegocioFinanceira as erro:
        raise _conflito_regra_negocio(erro) from erro
    if not removida:
        raise HTTPException(status_code=404, detail="Conta a receber não encontrada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/fluxo-caixa", response_model=list[FluxoCaixaOut])
def listar_fluxo_caixa(
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    try:
        return fluxo_caixa_service.listar_lancamentos(
            db, data_inicio, data_fim, skip, limit
        )
    except RegraNegocioFinanceira as erro:
        raise _conflito_regra_negocio(erro) from erro


@router.get("/resumo", response_model=ResumoFinanceiroOut)
def resumo_financeiro(
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    db: Session = Depends(get_db),
):
    try:
        return fluxo_caixa_service.resumo_periodo(db, data_inicio, data_fim)
    except RegraNegocioFinanceira as erro:
        raise _conflito_regra_negocio(erro) from erro
