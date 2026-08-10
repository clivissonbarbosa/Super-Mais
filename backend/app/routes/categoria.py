from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.Categoria import Categoria
from app.schemas.Categoria import CategoriaCreate, CategoriaOut
from backend.app.core.security import get_current_user

router = APIRouter(prefix="/categoria", tags=["categoria"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=CategoriaOut)
def criar_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    nova_categoria = Categoria(**categoria.dict())
    db.add(nova_categoria)
    db.commit()
    db.refresh(nova_categoria)
    return nova_categoria
