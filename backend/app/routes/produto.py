from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.Categoria import Categoria
from app.models.produto import Produto
from app.schemas.produto import ProdutoCreate, ProdutoOut


router = APIRouter(
    prefix="/produtos",
    tags=["Produtos"],
    dependencies=[Depends(get_current_user)],
)


def _buscar(db: Session, id_produto: int) -> Produto:
    produto = db.query(Produto).filter(Produto.id_produto == id_produto).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return produto


def _validar(db: Session, dados: ProdutoCreate, id_produto: int | None = None) -> None:
    if not db.query(Categoria).filter(
        Categoria.id_categoria == dados.id_categoria
    ).first():
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")
    existente = db.query(Produto).filter(Produto.codigo_barras == dados.codigo_barras.strip())
    if id_produto is not None:
        existente = existente.filter(Produto.id_produto != id_produto)
    if existente.first():
        raise HTTPException(status_code=409, detail="Código de barras já cadastrado.")


@router.post("/", response_model=ProdutoOut, status_code=status.HTTP_201_CREATED)
def criar_produto(dados: ProdutoCreate, db: Session = Depends(get_db)):
    _validar(db, dados)
    produto = Produto(**dados.model_dump())
    produto.nome = produto.nome.strip()
    produto.codigo_barras = produto.codigo_barras.strip()
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@router.get("/", response_model=list[ProdutoOut])
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(Produto).order_by(Produto.nome).all()


@router.get("/{id_produto}", response_model=ProdutoOut)
def buscar_produto(id_produto: int, db: Session = Depends(get_db)):
    return _buscar(db, id_produto)


@router.put("/{id_produto}", response_model=ProdutoOut)
def atualizar_produto(
    id_produto: int, dados: ProdutoCreate, db: Session = Depends(get_db)
):
    produto = _buscar(db, id_produto)
    _validar(db, dados, id_produto)
    for campo, valor in dados.model_dump().items():
        setattr(produto, campo, valor.strip() if isinstance(valor, str) else valor)
    db.commit()
    db.refresh(produto)
    return produto


@router.delete("/{id_produto}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_produto(id_produto: int, db: Session = Depends(get_db)):
    produto = _buscar(db, id_produto)
    try:
        db.delete(produto)
        db.commit()
    except IntegrityError as erro:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="O produto possui operações vinculadas e não pode ser excluído.",
        ) from erro
    return Response(status_code=status.HTTP_204_NO_CONTENT)
