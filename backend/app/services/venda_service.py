import unicodedata

from sqlalchemy.orm import Session

from app.models.Vendas import Venda
from app.schemas.Vendas import VendaCreate
from app.services import conta_receber, fluxo_caixa_service
from app.services.financeiro_exceptions import RegraNegocioFinanceira


PRAZO_PADRAO_RECEBIMENTO_DIAS = 30
FORMAS_PAGAMENTO = {
    "a vista": "a_vista",
    "dinheiro": "dinheiro",
    "pix": "pix",
    "debito": "cartao_debito",
    "cartao de debito": "cartao_debito",
    "credito": "cartao_credito",
    "cartao de credito": "cartao_credito",
    "boleto": "boleto",
    "a prazo": "a_prazo",
}
FORMAS_IMEDIATAS = {"a_vista", "dinheiro", "pix", "cartao_debito"}


def _normalizar_texto(valor: str) -> str:
    sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", valor)
        if unicodedata.category(caractere) != "Mn"
    )
    return " ".join(sem_acentos.lower().replace("_", " ").strip().split())


def normalizar_forma_pagamento(forma_pagamento: str) -> str:
    forma = FORMAS_PAGAMENTO.get(_normalizar_texto(forma_pagamento))
    if not forma:
        permitidas = ", ".join(sorted(set(FORMAS_PAGAMENTO.values())))
        raise RegraNegocioFinanceira(f"Forma de pagamento inválida. Use uma de: {permitidas}.")
    return forma


def criar_venda(db: Session, venda: VendaCreate) -> Venda:
    """Cria a venda, a conta a receber e, quando à vista, a entrada de caixa."""
    forma_pagamento = normalizar_forma_pagamento(venda.forma_pagamento)
    venda_imediata = forma_pagamento in FORMAS_IMEDIATAS

    try:
        db_venda = Venda(
            id_unidade=venda.id_unidade,
            id_usuario=venda.id_usuario,
            id_cliente=venda.id_cliente,
            id_produto=venda.id_produto,
            data_hora=venda.data_hora or fluxo_caixa_service.agora_utc(),
            valor_total=venda.valor_total,
            forma_pagamento=forma_pagamento,
        )
        db.add(db_venda)
        db.flush()

        conta = conta_receber.criar_conta_receber(
            db,
            id_venda=db_venda.id_venda,
            valor=db_venda.valor_total,
            prazo_dias=0 if venda_imediata else PRAZO_PADRAO_RECEBIMENTO_DIAS,
            commit=False,
        )
        if venda_imediata:
            conta.status_pagamento = "pago"
            fluxo_caixa_service.registrar_lancamento(
                db,
                id_conta_pagar=None,
                id_conta_receber=conta.id_conta_receber,
                tipo_lancamento="entrada",
                valor=conta.valor,
                commit=False,
            )

        db.commit()
        db.refresh(db_venda)
        return db_venda
    except Exception:
        db.rollback()
        raise


def listar_vendas(db: Session, skip: int = 0, limit: int = 100) -> list[Venda]:
    return db.query(Venda).order_by(Venda.data_hora.desc()).offset(skip).limit(limit).all()


def buscar_venda(db: Session, id_venda: int) -> Venda | None:
    return db.query(Venda).filter(Venda.id_venda == id_venda).first()
