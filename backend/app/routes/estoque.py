from app.models.User import Usuario
from app.core.security import get_current_user
from app.models.Estoque import Estoque
from app.schemas.Estoque import EstoqueCreate, EstoqueOut
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from  app.schemas.Estoque import  (
    EstoqueSaldoOut,
    EstoqueMovimentacaoCreate,
    EstoqueMovimentacaoOut,
    TipoMovimento,
)
router = APIRouter(prefix="/estoque", tags=["Estoque"], dependencies=[Depends(get_current_user)])

@router.post("/", response_model=EstoqueOut)
def criar_estoque(estoque: EstoqueCreate, db: Session = Depends(get_db)):

        novo = Estoque(**estoque.dict())
        db.add(novo)
        db.commit()
        db.refresh(novo)
        return novo

@router.get("/", response_model=list[EstoqueOut])
def listar_estoque(db: Session = Depends(get_db)):
    return db.query(Estoque).all()