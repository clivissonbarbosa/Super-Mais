"""modulos financeiro e compras

Revision ID: f2b7d9c1a410
Revises: e3830a282a7d
Create Date: 2026-08-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f2b7d9c1a410"
down_revision: str | None = "e3830a282a7d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fornecedor",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(), nullable=True),
        sa.Column("cnpj", sa.String(), nullable=True),
        sa.Column("endereco", sa.String(), nullable=True),
        sa.Column("telefone", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fornecedor_id", "fornecedor", ["id"], unique=False)
    op.create_index("ix_fornecedor_nome", "fornecedor", ["nome"], unique=True)
    op.create_index("ix_fornecedor_cnpj", "fornecedor", ["cnpj"], unique=True)

    op.create_table(
        "pedido_compra",
        sa.Column("id_pedido", sa.Integer(), nullable=False),
        sa.Column("id_fornecedor", sa.Integer(), nullable=False),
        sa.Column("data_pedido", sa.DateTime(), nullable=False),
        sa.Column("status_pedido", sa.String(), nullable=False),
        sa.Column("prazo_entrega_dias", sa.Integer(), nullable=False),
        sa.CheckConstraint("prazo_entrega_dias >= 0", name="ck_pedido_compra_prazo"),
        sa.CheckConstraint(
            "status_pedido IN ('pendente', 'aprovado', 'recebido', 'cancelado')",
            name="ck_pedido_compra_status",
        ),
        sa.ForeignKeyConstraint(["id_fornecedor"], ["fornecedor.id"]),
        sa.PrimaryKeyConstraint("id_pedido"),
    )
    op.create_table(
        "nota_fiscal",
        sa.Column("id_nota", sa.Integer(), nullable=False),
        sa.Column("id_pedido", sa.Integer(), nullable=False),
        sa.Column("numero_nota", sa.String(), nullable=False),
        sa.Column("data_emissao", sa.DateTime(), nullable=False),
        sa.Column("valor_total", sa.Float(), nullable=False),
        sa.CheckConstraint("valor_total > 0", name="ck_nota_fiscal_valor_positivo"),
        sa.ForeignKeyConstraint(["id_pedido"], ["pedido_compra.id_pedido"]),
        sa.PrimaryKeyConstraint("id_nota"),
        sa.UniqueConstraint("numero_nota"),
    )
    op.create_table(
        "venda_item",
        sa.Column("id_item", sa.Integer(), nullable=False),
        sa.Column("id_venda", sa.Integer(), nullable=False),
        sa.Column("id_produto", sa.Integer(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("preco_unitario", sa.Float(), nullable=False),
        sa.CheckConstraint("quantidade > 0", name="ck_venda_item_quantidade_positiva"),
        sa.CheckConstraint("preco_unitario > 0", name="ck_venda_item_preco_positivo"),
        sa.ForeignKeyConstraint(["id_produto"], ["produto.id_produto"]),
        sa.ForeignKeyConstraint(["id_venda"], ["venda.id_venda"]),
        sa.PrimaryKeyConstraint("id_item"),
    )
    op.create_table(
        "conta_pagar",
        sa.Column("id_conta_pagar", sa.Integer(), nullable=False),
        sa.Column("id_nota", sa.Integer(), nullable=False),
        sa.Column("data_vencimento", sa.DateTime(), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("status_pagamento", sa.String(), nullable=False),
        sa.CheckConstraint("valor > 0", name="ck_conta_pagar_valor_positivo"),
        sa.CheckConstraint(
            "status_pagamento IN ('pendente', 'pago', 'cancelado')",
            name="ck_conta_pagar_status",
        ),
        sa.ForeignKeyConstraint(["id_nota"], ["nota_fiscal.id_nota"]),
        sa.PrimaryKeyConstraint("id_conta_pagar"),
        sa.UniqueConstraint("id_nota", name="uq_conta_pagar_id_nota"),
    )
    op.create_table(
        "conta_receber",
        sa.Column("id_conta_receber", sa.Integer(), nullable=False),
        sa.Column("id_venda", sa.Integer(), nullable=False),
        sa.Column("data_vencimento", sa.DateTime(), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("status_pagamento", sa.String(), nullable=False),
        sa.CheckConstraint("valor > 0", name="ck_conta_receber_valor_positivo"),
        sa.CheckConstraint(
            "status_pagamento IN ('pendente', 'pago', 'cancelado')",
            name="ck_conta_receber_status",
        ),
        sa.ForeignKeyConstraint(["id_venda"], ["venda.id_venda"]),
        sa.PrimaryKeyConstraint("id_conta_receber"),
        sa.UniqueConstraint("id_venda", name="uq_conta_receber_id_venda"),
    )
    op.create_table(
        "fluxo_caixa",
        sa.Column("id_lancamento", sa.Integer(), nullable=False),
        sa.Column("id_conta_pagar", sa.Integer(), nullable=True),
        sa.Column("id_conta_receber", sa.Integer(), nullable=True),
        sa.Column("tipo_lancamento", sa.String(), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("data_confirmacao", sa.DateTime(), nullable=False),
        sa.CheckConstraint("valor > 0", name="ck_fluxo_caixa_valor_positivo"),
        sa.CheckConstraint(
            "(id_conta_pagar IS NOT NULL AND id_conta_receber IS NULL) OR "
            "(id_conta_pagar IS NULL AND id_conta_receber IS NOT NULL)",
            name="ck_fluxo_caixa_uma_origem",
        ),
        sa.CheckConstraint(
            "(id_conta_pagar IS NOT NULL AND tipo_lancamento = 'saida') OR "
            "(id_conta_receber IS NOT NULL AND tipo_lancamento = 'entrada')",
            name="ck_fluxo_caixa_tipo_origem",
        ),
        sa.ForeignKeyConstraint(["id_conta_pagar"], ["conta_pagar.id_conta_pagar"]),
        sa.ForeignKeyConstraint(["id_conta_receber"], ["conta_receber.id_conta_receber"]),
        sa.PrimaryKeyConstraint("id_lancamento"),
        sa.UniqueConstraint("id_conta_pagar", name="uq_fluxo_caixa_conta_pagar"),
        sa.UniqueConstraint("id_conta_receber", name="uq_fluxo_caixa_conta_receber"),
    )


def downgrade() -> None:
    op.drop_table("fluxo_caixa")
    op.drop_table("conta_receber")
    op.drop_table("conta_pagar")
    op.drop_table("venda_item")
    op.drop_table("nota_fiscal")
    op.drop_table("pedido_compra")
    op.drop_index("ix_fornecedor_cnpj", table_name="fornecedor")
    op.drop_index("ix_fornecedor_nome", table_name="fornecedor")
    op.drop_index("ix_fornecedor_id", table_name="fornecedor")
    op.drop_table("fornecedor")
