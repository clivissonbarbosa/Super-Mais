from sqlalchemy.orm import Session

from app.models.Venda_Item import VendaItem
from app.schemas.Venda_Item import VendaItemCreate
from app.services.financeiro_exceptions import RegraNegocioFinanceira


def adicionar_item(db: Session, item: VendaItemCreate) -> VendaItem:
    if item.quantidade <= 0 or item.preco_unitario <= 0:
        raise RegraNegocioFinanceira("Quantidade e preço unitário devem ser maiores que zero.")
    db_item = VendaItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def listar_itens_venda(db: Session, id_venda: int) -> list[VendaItem]:
    return db.query(VendaItem).filter(VendaItem.id_venda == id_venda).all()
