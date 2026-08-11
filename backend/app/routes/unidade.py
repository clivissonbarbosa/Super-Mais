from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.Unidade import Unidade
from app.schemas.Unidade import UnidadeCreate, UnidadeOut


router = APIRouter(
    prefix="/unidades",
    tags=["Unidades"],
    dependencies=[Depends(get_current_user)],
)


def _buscar(db: Session, id_unidade: int) -> Unidade:
    unidade = db.query(Unidade).filter(Unidade.id_unidade == id_unidade).first()
    if not unidade:
        raise HTTPException(status_code=404, detail="Unidade não encontrada.")
    return unidade


@router.post("/", response_model=UnidadeOut, status_code=status.HTTP_201_CREATED)
def criar_unidade(dados: UnidadeCreate, db: Session = Depends(get_db)):
    nome = dados.nome.strip()
    if db.query(Unidade).filter(Unidade.nome.ilike(nome)).first():
        raise HTTPException(status_code=409, detail="Unidade já cadastrada.")
    unidade = Unidade(nome=nome, tipo=dados.tipo)
    db.add(unidade)
    db.commit()
    db.refresh(unidade)
    return unidade


@router.get("/", response_model=list[UnidadeOut])
def listar_unidades(db: Session = Depends(get_db)):
    return db.query(Unidade).order_by(Unidade.nome).all()


@router.get("/{id_unidade}", response_model=UnidadeOut)
def buscar_unidade(id_unidade: int, db: Session = Depends(get_db)):
    return _buscar(db, id_unidade)


@router.put("/{id_unidade}", response_model=UnidadeOut)
def atualizar_unidade(
    id_unidade: int, dados: UnidadeCreate, db: Session = Depends(get_db)
):
    unidade = _buscar(db, id_unidade)
    nome = dados.nome.strip()
    existente = (
        db.query(Unidade)
        .filter(Unidade.nome.ilike(nome), Unidade.id_unidade != id_unidade)
        .first()
    )
    if existente:
        raise HTTPException(status_code=409, detail="Unidade já cadastrada.")
    unidade.nome = nome
    unidade.tipo = dados.tipo
    db.commit()
    db.refresh(unidade)
    return unidade


@router.delete("/{id_unidade}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_unidade(id_unidade: int, db: Session = Depends(get_db)):
    unidade = _buscar(db, id_unidade)
    try:
        db.delete(unidade)
        db.commit()
    except IntegrityError as erro:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A unidade possui operações vinculadas e não pode ser excluída.",
        ) from erro
    return Response(status_code=status.HTTP_204_NO_CONTENT)
