from sqlalchemy.orm import Session

from app.models.Estoque import EstoqueMovimentacao, EstoqueSaldo
from app.models.produto import Produto
from app.models.Unidade import Unidade
from app.services.financeiro_exceptions import RegraNegocioFinanceira


TIPOS_MOVIMENTO = {"entrada", "saida", "perda"}


def buscar_saldo(
    db: Session,
    id_produto: int,
    id_unidade: int,
    *,
    bloquear: bool = False,
) -> EstoqueSaldo | None:
    query = db.query(EstoqueSaldo).filter(
        EstoqueSaldo.id_produto == id_produto,
        EstoqueSaldo.id_unidade == id_unidade,
    )
    if bloquear:
        query = query.with_for_update()
    return query.first()


def buscar_saldo_por_id(db: Session, id_saldo: int) -> EstoqueSaldo | None:
    return db.query(EstoqueSaldo).filter(EstoqueSaldo.id_saldo == id_saldo).first()


def listar_saldos(
    db: Session,
    *,
    id_unidade: int | None = None,
    somente_abaixo_minimo: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> list[EstoqueSaldo]:
    query = db.query(EstoqueSaldo)
    if id_unidade is not None:
        query = query.filter(EstoqueSaldo.id_unidade == id_unidade)
    if somente_abaixo_minimo:
        query = query.filter(EstoqueSaldo.quantidade_atual <= EstoqueSaldo.estoque_minimo)
    return (
        query.order_by(EstoqueSaldo.id_unidade, EstoqueSaldo.id_produto)
        .offset(skip)
        .limit(limit)
        .all()
    )


def listar_movimentacoes(
    db: Session,
    *,
    id_produto: int | None = None,
    id_unidade: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[EstoqueMovimentacao]:
    query = db.query(EstoqueMovimentacao)
    if id_produto is not None:
        query = query.filter(EstoqueMovimentacao.id_produto == id_produto)
    if id_unidade is not None:
        query = query.filter(EstoqueMovimentacao.id_unidade == id_unidade)
    return (
        query.order_by(EstoqueMovimentacao.data_movimentacao.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def atualizar_estoque_minimo(
    db: Session, id_saldo: int, estoque_minimo: int
) -> EstoqueSaldo | None:
    saldo = buscar_saldo_por_id(db, id_saldo)
    if not saldo:
        return None
    if estoque_minimo < 0:
        raise RegraNegocioFinanceira("O estoque mínimo não pode ser negativo.")
    saldo.estoque_minimo = estoque_minimo
    db.commit()
    db.refresh(saldo)
    return saldo


def registrar_movimentacao(
    db: Session,
    *,
    id_produto: int,
    id_unidade: int,
    tipo_movimento: str,
    quantidade: int,
    motivo: str | None = None,
    id_usuario: int | None = None,
    referencia_tipo: str | None = None,
    referencia_id: int | None = None,
    commit: bool = True,
) -> EstoqueMovimentacao:
    tipo = tipo_movimento.strip().lower()
    if tipo not in TIPOS_MOVIMENTO:
        raise RegraNegocioFinanceira("Tipo de movimento de estoque inválido.")
    if quantidade <= 0:
        raise RegraNegocioFinanceira("A quantidade movimentada deve ser maior que zero.")
    if not db.query(Produto).filter(Produto.id_produto == id_produto).first():
        raise RegraNegocioFinanceira("Produto não encontrado.")
    if not db.query(Unidade).filter(Unidade.id_unidade == id_unidade).first():
        raise RegraNegocioFinanceira("Unidade não encontrada.")

    saldo = buscar_saldo(db, id_produto, id_unidade, bloquear=True)
    if saldo is None:
        if tipo != "entrada":
            raise RegraNegocioFinanceira("Não existe saldo disponível para este produto na unidade.")
        saldo = EstoqueSaldo(
            id_produto=id_produto,
            id_unidade=id_unidade,
            quantidade_atual=0,
            estoque_minimo=0,
        )
        db.add(saldo)
        db.flush()

    if tipo == "entrada":
        saldo.quantidade_atual += quantidade
    else:
        if saldo.quantidade_atual < quantidade:
            raise RegraNegocioFinanceira(
                f"Estoque insuficiente. Disponível: {saldo.quantidade_atual}; solicitado: {quantidade}."
            )
        saldo.quantidade_atual -= quantidade

    movimento = EstoqueMovimentacao(
        id_produto=id_produto,
        id_unidade=id_unidade,
        id_usuario=id_usuario,
        tipo_movimento=tipo,
        quantidade=quantidade,
        motivo=motivo,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
    )
    db.add(movimento)
    db.flush()
    if commit:
        db.commit()
        db.refresh(movimento)
    return movimento
