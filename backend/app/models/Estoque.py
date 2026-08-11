from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)

from app.database import Base


class EstoqueSaldo(Base):
    __tablename__ = "estoque_saldo"
    __table_args__ = (
        UniqueConstraint(
            "id_produto", "id_unidade", name="uq_estoque_saldo_produto_unidade"
        ),
        CheckConstraint(
            "quantidade_atual >= 0", name="ck_estoque_saldo_quantidade_nao_negativa"
        ),
        CheckConstraint(
            "estoque_minimo >= 0", name="ck_estoque_saldo_minimo_nao_negativo"
        ),
    )

    id_saldo = Column(Integer, primary_key=True)
    id_produto = Column(
        Integer, ForeignKey("produto.id_produto"), nullable=False, index=True
    )
    id_unidade = Column(
        Integer, ForeignKey("unidade.id_unidade"), nullable=False, index=True
    )
    quantidade_atual = Column(Integer, nullable=False, default=0)
    estoque_minimo = Column(Integer, nullable=False, default=0)


class EstoqueMovimentacao(Base):
    __tablename__ = "estoque_movimentacao"
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="ck_estoque_movimentacao_quantidade"),
        CheckConstraint(
            "tipo_movimento IN ('entrada', 'saida', 'perda')",
            name="ck_estoque_movimentacao_tipo",
        ),
    )

    id_movimentacao = Column(Integer, primary_key=True)
    id_produto = Column(
        Integer, ForeignKey("produto.id_produto"), nullable=False, index=True
    )
    id_unidade = Column(
        Integer, ForeignKey("unidade.id_unidade"), nullable=False, index=True
    )
    id_usuario = Column(
        Integer, ForeignKey("usuario.id_usuario"), nullable=True, index=True
    )
    tipo_movimento = Column(String, nullable=False)
    quantidade = Column(Integer, nullable=False)
    data_movimentacao = Column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )
    motivo = Column(String, nullable=True)
    referencia_tipo = Column(String, nullable=True)
    referencia_id = Column(Integer, nullable=True)
