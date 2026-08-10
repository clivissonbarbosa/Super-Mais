from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.produto import Produto
from app.schemas.produto import ProdutoCreate, ProdutoOut
from app.core.security import get_current_user
from app.models.User import Usuario
router = APIRouter(prefix="/produtos", tags=["Produtos"],dependencies=[Depends(get_current_user)])

print("Usuário atual: {}", )
@router.post("/", response_model=ProdutoOut)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    novo = Produto(**produto.dict())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@router.get("/", response_model=list[ProdutoOut])
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(Produto).all()