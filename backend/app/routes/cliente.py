from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.Cliente import Cliente
from app.schemas.Cliente import ClienteCreate, ClienteOut


router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
    dependencies=[Depends(get_current_user)],
)


def _buscar(db: Session, id_cliente: int) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id_cliente == id_cliente).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return cliente


@router.post("/", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def criar_cliente(dados: ClienteCreate, db: Session = Depends(get_db)):
    cpf = "".join(caractere for caractere in dados.cpf if caractere.isdigit())
    if len(cpf) != 11:
        raise HTTPException(status_code=422, detail="CPF deve possuir 11 dígitos.")
    if db.query(Cliente).filter(Cliente.cpf == cpf).first():
        raise HTTPException(status_code=409, detail="CPF já cadastrado.")
    cliente = Cliente(
        cpf=cpf,
        nome=dados.nome.strip(),
        segmento_marketing=(dados.segmento_marketing or None),
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.get("/", response_model=list[ClienteOut])
def listar_clientes(db: Session = Depends(get_db)):
    return db.query(Cliente).order_by(Cliente.nome).all()


@router.get("/{id_cliente}", response_model=ClienteOut)
def buscar_cliente(id_cliente: int, db: Session = Depends(get_db)):
    return _buscar(db, id_cliente)


@router.put("/{id_cliente}", response_model=ClienteOut)
def atualizar_cliente(
    id_cliente: int, dados: ClienteCreate, db: Session = Depends(get_db)
):
    cliente = _buscar(db, id_cliente)
    cpf = "".join(caractere for caractere in dados.cpf if caractere.isdigit())
    if len(cpf) != 11:
        raise HTTPException(status_code=422, detail="CPF deve possuir 11 dígitos.")
    existente = db.query(Cliente).filter(
        Cliente.cpf == cpf, Cliente.id_cliente != id_cliente
    ).first()
    if existente:
        raise HTTPException(status_code=409, detail="CPF já cadastrado.")
    cliente.cpf = cpf
    cliente.nome = dados.nome.strip()
    cliente.segmento_marketing = dados.segmento_marketing or None
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{id_cliente}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_cliente(id_cliente: int, db: Session = Depends(get_db)):
    cliente = _buscar(db, id_cliente)
    try:
        db.delete(cliente)
        db.commit()
    except IntegrityError as erro:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="O cliente possui vendas vinculadas e não pode ser excluído.",
        ) from erro
    return Response(status_code=status.HTTP_204_NO_CONTENT)
