"""integra estoque, itens de compra e rastreabilidade

Revision ID: c1e8a4d2f930
Revises: 9705b5761b85
Create Date: 2026-08-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c1e8a4d2f930"
down_revision: str | None = "9705b5761b85"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "pedido_compra", sa.Column("id_unidade", sa.Integer(), nullable=True)
    )
    op.add_column(
        "pedido_compra", sa.Column("id_usuario", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_pedido_compra_unidade",
        "pedido_compra",
        "unidade",
        ["id_unidade"],
        ["id_unidade"],
    )
    op.create_foreign_key(
        "fk_pedido_compra_usuario",
        "pedido_compra",
        "usuario",
        ["id_usuario"],
        ["id_usuario"],
    )

    op.create_table(
        "pedido_compra_item",
        sa.Column("id_item", sa.Integer(), nullable=False),
        sa.Column("id_pedido", sa.Integer(), nullable=False),
        sa.Column("id_produto", sa.Integer(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("preco_unitario", sa.Float(), nullable=False),
        sa.CheckConstraint(
            "quantidade > 0", name="ck_pedido_compra_item_quantidade"
        ),
        sa.CheckConstraint(
            "preco_unitario > 0", name="ck_pedido_compra_item_preco_unitario"
        ),
        sa.ForeignKeyConstraint(["id_pedido"], ["pedido_compra.id_pedido"]),
        sa.ForeignKeyConstraint(["id_produto"], ["produto.id_produto"]),
        sa.PrimaryKeyConstraint("id_item"),
        sa.UniqueConstraint(
            "id_pedido", "id_produto", name="uq_pedido_compra_item_produto"
        ),
    )
    op.create_index(
        "ix_pedido_compra_item_id_pedido",
        "pedido_compra_item",
        ["id_pedido"],
    )
    op.create_index(
        "ix_pedido_compra_item_id_produto",
        "pedido_compra_item",
        ["id_produto"],
    )

    op.create_table(
        "estoque_saldo",
        sa.Column("id_saldo", sa.Integer(), nullable=False),
        sa.Column("id_produto", sa.Integer(), nullable=False),
        sa.Column("id_unidade", sa.Integer(), nullable=False),
        sa.Column("quantidade_atual", sa.Integer(), nullable=False),
        sa.Column("estoque_minimo", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "quantidade_atual >= 0", name="ck_estoque_saldo_quantidade_nao_negativa"
        ),
        sa.CheckConstraint(
            "estoque_minimo >= 0", name="ck_estoque_saldo_minimo_nao_negativo"
        ),
        sa.ForeignKeyConstraint(["id_produto"], ["produto.id_produto"]),
        sa.ForeignKeyConstraint(["id_unidade"], ["unidade.id_unidade"]),
        sa.PrimaryKeyConstraint("id_saldo"),
        sa.UniqueConstraint(
            "id_produto", "id_unidade", name="uq_estoque_saldo_produto_unidade"
        ),
    )
    op.create_index("ix_estoque_saldo_id_produto", "estoque_saldo", ["id_produto"])
    op.create_index("ix_estoque_saldo_id_unidade", "estoque_saldo", ["id_unidade"])

    op.create_table(
        "estoque_movimentacao",
        sa.Column("id_movimentacao", sa.Integer(), nullable=False),
        sa.Column("id_produto", sa.Integer(), nullable=False),
        sa.Column("id_unidade", sa.Integer(), nullable=False),
        sa.Column("id_usuario", sa.Integer(), nullable=True),
        sa.Column("tipo_movimento", sa.String(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column(
            "data_movimentacao",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("motivo", sa.String(), nullable=True),
        sa.Column("referencia_tipo", sa.String(), nullable=True),
        sa.Column("referencia_id", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "quantidade > 0", name="ck_estoque_movimentacao_quantidade"
        ),
        sa.CheckConstraint(
            "tipo_movimento IN ('entrada', 'saida', 'perda')",
            name="ck_estoque_movimentacao_tipo",
        ),
        sa.ForeignKeyConstraint(["id_produto"], ["produto.id_produto"]),
        sa.ForeignKeyConstraint(["id_unidade"], ["unidade.id_unidade"]),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuario.id_usuario"]),
        sa.PrimaryKeyConstraint("id_movimentacao"),
    )
    op.create_index(
        "ix_estoque_movimentacao_id_produto",
        "estoque_movimentacao",
        ["id_produto"],
    )
    op.create_index(
        "ix_estoque_movimentacao_id_unidade",
        "estoque_movimentacao",
        ["id_unidade"],
    )
    op.create_index(
        "ix_estoque_movimentacao_id_usuario",
        "estoque_movimentacao",
        ["id_usuario"],
    )
    op.create_index(
        "ix_estoque_movimentacao_data_movimentacao",
        "estoque_movimentacao",
        ["data_movimentacao"],
    )

    op.add_column(
        "fluxo_caixa", sa.Column("id_usuario", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_fluxo_caixa_usuario",
        "fluxo_caixa",
        "usuario",
        ["id_usuario"],
        ["id_usuario"],
    )

    op.create_unique_constraint(
        "uq_nota_fiscal_id_pedido", "nota_fiscal", ["id_pedido"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_nota_fiscal_id_pedido", "nota_fiscal", type_="unique")
    op.drop_constraint("fk_fluxo_caixa_usuario", "fluxo_caixa", type_="foreignkey")
    op.drop_column("fluxo_caixa", "id_usuario")

    op.drop_index(
        "ix_estoque_movimentacao_data_movimentacao",
        table_name="estoque_movimentacao",
    )
    op.drop_index(
        "ix_estoque_movimentacao_id_usuario", table_name="estoque_movimentacao"
    )
    op.drop_index(
        "ix_estoque_movimentacao_id_unidade", table_name="estoque_movimentacao"
    )
    op.drop_index(
        "ix_estoque_movimentacao_id_produto", table_name="estoque_movimentacao"
    )
    op.drop_table("estoque_movimentacao")

    op.drop_index("ix_estoque_saldo_id_unidade", table_name="estoque_saldo")
    op.drop_index("ix_estoque_saldo_id_produto", table_name="estoque_saldo")
    op.drop_table("estoque_saldo")

    op.drop_index(
        "ix_pedido_compra_item_id_produto", table_name="pedido_compra_item"
    )
    op.drop_index(
        "ix_pedido_compra_item_id_pedido", table_name="pedido_compra_item"
    )
    op.drop_table("pedido_compra_item")

    op.drop_constraint("fk_pedido_compra_usuario", "pedido_compra", type_="foreignkey")
    op.drop_constraint("fk_pedido_compra_unidade", "pedido_compra", type_="foreignkey")
    op.drop_column("pedido_compra", "id_usuario")
    op.drop_column("pedido_compra", "id_unidade")
