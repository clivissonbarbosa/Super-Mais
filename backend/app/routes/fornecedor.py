from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.Fornecedor import Fornecedor
from app.schemas.Fornecedor import FornecedorCreate, FornecedorOut


router = APIRouter(
    prefix="/fornecedores",
    tags=["Fornecedores"],
    dependencies=[Depends(get_current_user)],
)


def _buscar(db: Session, fornecedor_id: int) -> Fornecedor:
    fornecedor = db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()
    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")
    return fornecedor


def _validar_unicidade(
    db: Session, dados: FornecedorCreate, fornecedor_id: int | None = None
) -> None:
    consulta = db.query(Fornecedor).filter(
        (Fornecedor.nome.ilike(dados.nome.strip()))
        | (Fornecedor.cnpj == dados.cnpj.strip())
    )
    if fornecedor_id is not None:
        consulta = consulta.filter(Fornecedor.id != fornecedor_id)
    if consulta.first():
        raise HTTPException(
            status_code=409,
            detail="Já existe fornecedor com o mesmo nome ou CNPJ.",
        )


@router.post("/", response_model=FornecedorOut, status_code=status.HTTP_201_CREATED)
def criar_fornecedor(dados: FornecedorCreate, db: Session = Depends(get_db)):
    _validar_unicidade(db, dados)
    fornecedor = Fornecedor(
        nome=dados.nome.strip(),
        cnpj=dados.cnpj.strip(),
        endereco=dados.endereco.strip(),
        telefone=dados.telefone.strip(),
    )
    db.add(fornecedor)
    db.commit()
    db.refresh(fornecedor)
    return fornecedor


@router.get("/", response_model=list[FornecedorOut])
def listar_fornecedores(db: Session = Depends(get_db)):
    return db.query(Fornecedor).order_by(Fornecedor.nome).all()


@router.get("/{fornecedor_id}", response_model=FornecedorOut)
def buscar_fornecedor(fornecedor_id: int, db: Session = Depends(get_db)):
    return _buscar(db, fornecedor_id)


@router.put("/{fornecedor_id}", response_model=FornecedorOut)
def atualizar_fornecedor(
    fornecedor_id: int,
    dados: FornecedorCreate,
    db: Session = Depends(get_db),
):
    fornecedor = _buscar(db, fornecedor_id)
    _validar_unicidade(db, dados, fornecedor_id)
    fornecedor.nome = dados.nome.strip()
    fornecedor.cnpj = dados.cnpj.strip()
    fornecedor.endereco = dados.endereco.strip()
    fornecedor.telefone = dados.telefone.strip()
    db.commit()
    db.refresh(fornecedor)
    return fornecedor


@router.delete("/{fornecedor_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_fornecedor(fornecedor_id: int, db: Session = Depends(get_db)):
    fornecedor = _buscar(db, fornecedor_id)
    try:
        db.delete(fornecedor)
        db.commit()
    except IntegrityError as erro:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="O fornecedor possui pedidos vinculados e não pode ser excluído.",
        ) from erro
    return Response(status_code=status.HTTP_204_NO_CONTENT)
