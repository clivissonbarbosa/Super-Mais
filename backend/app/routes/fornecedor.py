from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.Fornecedor import Fornecedor
from app.schemas.Fornecedor import FornecedorCreate, FornecedorOut

router = APIRouter(prefix="/fornecedores", tags=["Fornecedores"])

@router.post("/", response_model=FornecedorOut)
def criar_fornecedor(fornecedor: FornecedorCreate, db: Session = Depends(get_db)):
    novo = Fornecedor(**fornecedor.dict())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo
@router.get("/", response_model=list[FornecedorOut])
def listar_fornecedores(db: Session = Depends(get_db)):
    return db.query(Fornecedor).all()

@router.get("/{fornecedor_id}", response_model=FornecedorOut)
def listar_fornecedor_por_id(fornecedor_id: int, db: Session = Depends(get_db)):
    return db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()

@router.put("/{fornecedor_id}", response_model=FornecedorOut)
def atualizar_fornecedor(fornecedor_id: int, fornecedor: FornecedorCreate, db: Session = Depends(get_db)):
    fornecedor_db = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if fornecedor_db:
        for key, value in fornecedor.dict().items():
            setattr(fornecedor_db, key, value)
        db.commit()
        db.refresh(fornecedor_db)
    return fornecedor_db

@router.delete("/{fornecedor_id}", response_model=FornecedorOut)
def deletar_fornecedor(fornecedor_id: int, db: Session = Depends(get_db)):
    fornecedor_db = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if fornecedor_db:
        db.delete(fornecedor_db)
        db.commit()
    return fornecedor_db