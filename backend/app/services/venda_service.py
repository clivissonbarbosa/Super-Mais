import unicodedata

from sqlalchemy.orm import Session, selectinload

from app.models.Cliente import Cliente
from app.models.Unidade import Unidade
from app.models.User import Usuario
from app.models.Venda_Item import VendaItem
from app.models.Vendas import Venda
from app.models.produto import Produto
from app.schemas.Vendas import VendaCreate
from app.services import conta_receber, estoque_service, fluxo_caixa_service
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
        raise RegraNegocioFinanceira(
            f"Forma de pagamento inválida. Use uma de: {permitidas}."
        )
    return forma


def _validar_referencias(
    db: Session,
    *,
    id_unidade: int,
    id_usuario: int,
    id_cliente: int | None,
) -> None:
    if not db.query(Unidade).filter(Unidade.id_unidade == id_unidade).first():
        raise RegraNegocioFinanceira("Unidade não encontrada.")
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario or usuario.ativo is False:
        raise RegraNegocioFinanceira("Usuário não encontrado ou inativo.")
    if id_cliente is not None and not db.query(Cliente).filter(
        Cliente.id_cliente == id_cliente
    ).first():
        raise RegraNegocioFinanceira("Cliente não encontrado.")


def criar_venda(
    db: Session,
    venda: VendaCreate,
    *,
    id_usuario: int | None = None,
) -> Venda:
    """Cria venda, itens, saída de estoque e recebível na mesma transação."""
    usuario_operacao = id_usuario or venda.id_usuario
    if usuario_operacao is None:
        raise RegraNegocioFinanceira("A venda precisa estar associada a um usuário.")
    _validar_referencias(
        db,
        id_unidade=venda.id_unidade,
        id_usuario=usuario_operacao,
        id_cliente=venda.id_cliente,
    )

    forma_pagamento = normalizar_forma_pagamento(venda.forma_pagamento)
    venda_imediata = forma_pagamento in FORMAS_IMEDIATAS

    produtos_venda = [item.id_produto for item in venda.itens]
    if len(produtos_venda) != len(set(produtos_venda)):
        raise RegraNegocioFinanceira("O mesmo produto não pode aparecer duas vezes na venda.")

    produtos_por_id: dict[int, Produto] = {}
    if produtos_venda:
        produtos_por_id = {
            produto.id_produto: produto
            for produto in db.query(Produto)
            .filter(Produto.id_produto.in_(produtos_venda))
            .all()
        }
        faltantes = sorted(set(produtos_venda) - set(produtos_por_id))
        if faltantes:
            raise RegraNegocioFinanceira(
                f"Produtos não encontrados na venda: {', '.join(map(str, faltantes))}."
            )
        if any(produto.preco_venda is None or produto.preco_venda <= 0 for produto in produtos_por_id.values()):
            raise RegraNegocioFinanceira("Todos os produtos precisam ter preço de venda válido.")
        valor_calculado = round(
            sum(
                item.quantidade * produtos_por_id[item.id_produto].preco_venda
                for item in venda.itens
            ),
            2,
        )
        if venda.valor_total is not None and abs(venda.valor_total - valor_calculado) > 0.01:
            raise RegraNegocioFinanceira(
                f"O valor da venda deve coincidir com os itens: {valor_calculado:.2f}."
            )
        valor_total = valor_calculado
    else:
        if venda.valor_total is None:
            raise RegraNegocioFinanceira("Informe os itens ou o valor total da venda.")
        valor_total = venda.valor_total

    try:
        db_venda = Venda(
            id_unidade=venda.id_unidade,
            id_usuario=usuario_operacao,
            id_cliente=venda.id_cliente,
            id_produto=(venda.itens[0].id_produto if venda.itens else venda.id_produto),
            data_hora=venda.data_hora or fluxo_caixa_service.agora_utc(),
            valor_total=valor_total,
            forma_pagamento=forma_pagamento,
        )
        db.add(db_venda)
        db.flush()

        for item in venda.itens:
            produto = produtos_por_id[item.id_produto]
            db.add(
                VendaItem(
                    id_venda=db_venda.id_venda,
                    id_produto=item.id_produto,
                    quantidade=item.quantidade,
                    preco_unitario=produto.preco_venda,
                )
            )
            estoque_service.registrar_movimentacao(
                db,
                id_produto=item.id_produto,
                id_unidade=venda.id_unidade,
                tipo_movimento="saida",
                quantidade=item.quantidade,
                motivo=f"Venda #{db_venda.id_venda}",
                id_usuario=usuario_operacao,
                referencia_tipo="venda",
                referencia_id=db_venda.id_venda,
                commit=False,
            )

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
                id_usuario=usuario_operacao,
                commit=False,
            )

        db.commit()
        return buscar_venda(db, db_venda.id_venda)
    except Exception:
        db.rollback()
        raise


def listar_vendas(db: Session, skip: int = 0, limit: int = 100) -> list[Venda]:
    return (
        db.query(Venda)
        .options(selectinload(Venda.itens))
        .order_by(Venda.data_hora.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def buscar_venda(db: Session, id_venda: int) -> Venda | None:
    return (
        db.query(Venda)
        .options(selectinload(Venda.itens))
        .filter(Venda.id_venda == id_venda)
        .first()
    )
