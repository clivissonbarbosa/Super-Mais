from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.Categoria import Categoria
from app.schemas.Categoria import CategoriaCreate, CategoriaOut


router = APIRouter(
    prefix="/categoria",
    tags=["Categorias"],
    dependencies=[Depends(get_current_user)],
)


def _buscar(db: Session, id_categoria: int) -> Categoria:
    categoria = db.query(Categoria).filter(Categoria.id_categoria == id_categoria).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    return categoria


@router.post("/", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def criar_categoria(dados: CategoriaCreate, db: Session = Depends(get_db)):
    nome = dados.nome.strip()
    if db.query(Categoria).filter(Categoria.nome.ilike(nome)).first():
        raise HTTPException(status_code=409, detail="Categoria já cadastrada.")
    categoria = Categoria(nome=nome, margem_lucro=dados.margem_lucro)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.get("/", response_model=list[CategoriaOut])
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(Categoria).order_by(Categoria.nome).all()


@router.get("/{id_categoria}", response_model=CategoriaOut)
def buscar_categoria(id_categoria: int, db: Session = Depends(get_db)):
    return _buscar(db, id_categoria)


@router.put("/{id_categoria}", response_model=CategoriaOut)
def atualizar_categoria(
    id_categoria: int, dados: CategoriaCreate, db: Session = Depends(get_db)
):
    categoria = _buscar(db, id_categoria)
    nome = dados.nome.strip()
    existente = (
        db.query(Categoria)
        .filter(Categoria.nome.ilike(nome), Categoria.id_categoria != id_categoria)
        .first()
    )
    if existente:
        raise HTTPException(status_code=409, detail="Categoria já cadastrada.")
    categoria.nome = nome
    categoria.margem_lucro = dados.margem_lucro
    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/{id_categoria}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_categoria(id_categoria: int, db: Session = Depends(get_db)):
    categoria = _buscar(db, id_categoria)
    try:
        db.delete(categoria)
        db.commit()
    except IntegrityError as erro:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A categoria possui produtos vinculados e não pode ser excluída.",
        ) from erro
    return Response(status_code=status.HTTP_204_NO_CONTENT)
