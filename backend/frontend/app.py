import os
import sys
from datetime import date, datetime, time
from pathlib import Path

import pandas as pd
import streamlit as st

# Garante que o import use o api_client local desta pasta.
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from api_client import ApiClient, ApiError


st.set_page_config(
    page_title="SuperMais Financeiro",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {padding-top: 2rem; padding-bottom: 3rem;}
        [data-testid="stMetric"] {
            background: var(--secondary-background-color);
            border: 1px solid rgba(128, 128, 128, 0.28);
            border-left: 4px solid #2e8b57;
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
        }
        [data-testid="stMetricLabel"] p {
            color: var(--text-color) !important;
            opacity: 0.72;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: var(--text-color) !important;
            font-weight: 700;
        }
        .app-subtitle {
            color: var(--text-color);
            opacity: 0.68;
            margin-top: -12px;
            margin-bottom: 24px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def moeda(valor: float | int | None) -> str:
    numero = float(valor or 0)
    formatado = f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatado}"


def preparar_tabela(registros: list[dict], colunas: dict[str, str]) -> pd.DataFrame:
    if not registros:
        return pd.DataFrame(columns=list(colunas.values()))
    tabela = pd.DataFrame(registros)
    tabela = tabela[[coluna for coluna in colunas if coluna in tabela.columns]].rename(
        columns=colunas
    )
    for coluna in ["Vencimento", "Confirmação", "Emissão", "Data do pedido", "Data"]:
        if coluna in tabela.columns:
            tabela[coluna] = pd.to_datetime(tabela[coluna], errors="coerce").dt.strftime(
                "%d/%m/%Y %H:%M"
            )
    if "Valor" in tabela.columns:
        tabela["Valor"] = tabela["Valor"].map(moeda)
    return tabela


def parametros_periodo() -> dict[str, str]:
    usar_periodo = st.checkbox("Filtrar por período", value=False)
    if not usar_periodo:
        return {}
    coluna_inicio, coluna_fim = st.columns(2)
    hoje = date.today()
    inicio = coluna_inicio.date_input("Data inicial", value=hoje.replace(day=1))
    fim = coluna_fim.date_input("Data final", value=hoje)
    return {
        "data_inicio": datetime.combine(inicio, time.min).isoformat(),
        "data_fim": datetime.combine(fim, time.max).isoformat(),
    }


def pagina_visao_geral(api: ApiClient) -> None:
    st.title("Visão geral financeira")
    st.markdown(
        '<p class="app-subtitle">Caixa realizado, obrigações e recebíveis da SuperMais.</p>',
        unsafe_allow_html=True,
    )
    parametros = parametros_periodo()
    try:
        resumo = api.get("/financeiro/resumo", params=parametros)
        fluxo = api.get(
            "/financeiro/fluxo-caixa", params={**parametros, "skip": 0, "limit": 100}
        )
    except ApiError as erro:
        st.error(str(erro))
        return

    primeira_linha = st.columns(3)
    primeira_linha[0].metric("Entradas", moeda(resumo["entradas"]))
    primeira_linha[1].metric("Saídas", moeda(resumo["saidas"]))
    primeira_linha[2].metric("Saldo realizado", moeda(resumo["saldo"]))

    segunda_linha = st.columns(3)
    segunda_linha[0].metric(
        "A receber", moeda(resumo["contas_receber_pendentes"])
    )
    segunda_linha[1].metric("A pagar", moeda(resumo["contas_pagar_pendentes"]))
    segunda_linha[2].metric(
        "Recebíveis vencidos", moeda(resumo["contas_receber_vencidas"])
    )

    st.subheader("Entradas e saídas")
    grafico = pd.DataFrame(
        {
            "Tipo": ["Entradas", "Saídas"],
            "Valor": [resumo["entradas"], resumo["saidas"]],
        }
    ).set_index("Tipo")
    st.bar_chart(grafico, color="#1f7a4d")

    st.subheader("Últimos lançamentos")
    tabela = preparar_tabela(
        fluxo,
        {
            "id_lancamento": "ID",
            "tipo_lancamento": "Tipo",
            "valor": "Valor",
            "data_confirmacao": "Confirmação",
            "id_conta_pagar": "Conta a pagar",
            "id_conta_receber": "Conta a receber",
        },
    )
    if tabela.empty:
        st.info("Ainda não há movimentações de caixa para os filtros selecionados.")
    else:
        st.dataframe(tabela, use_container_width=True, hide_index=True)


def pagina_contas(api: ApiClient, tipo: str) -> None:
    pagar = tipo == "pagar"
    titulo = "Contas a pagar" if pagar else "Contas a receber"
    endpoint = "/financeiro/contas-pagar" if pagar else "/financeiro/contas-receber"
    campo_id = "id_conta_pagar" if pagar else "id_conta_receber"
    campo_origem = "id_nota" if pagar else "id_venda"

    st.title(titulo)
    st.markdown(
        '<p class="app-subtitle">Consulte vencimentos e confirme as baixas financeiras.</p>',
        unsafe_allow_html=True,
    )

    coluna_status, coluna_vencidas = st.columns([2, 1])
    status_selecionado = coluna_status.selectbox(
        "Status", ["Todos", "Pendente", "Pago", "Cancelado"], key=f"status_{tipo}"
    )
    somente_vencidas = coluna_vencidas.checkbox(
        "Somente vencidas", value=False, key=f"vencidas_{tipo}"
    )
    parametros: dict[str, object] = {
        "somente_vencidas": somente_vencidas,
        "skip": 0,
        "limit": 500,
    }
    if status_selecionado != "Todos":
        parametros["status_pagamento"] = status_selecionado.lower()

    try:
        contas = api.get(endpoint, params=parametros)
    except ApiError as erro:
        st.error(str(erro))
        return

    tabela = preparar_tabela(
        contas,
        {
            campo_id: "ID",
            campo_origem: "Nota fiscal" if pagar else "Venda",
            "data_vencimento": "Vencimento",
            "valor": "Valor",
            "status_pagamento": "Status",
        },
    )
    if tabela.empty:
        st.info("Nenhuma conta encontrada.")
    else:
        st.dataframe(tabela, use_container_width=True, hide_index=True)

    pendentes = [conta for conta in contas if conta["status_pagamento"] == "pendente"]
    st.subheader("Confirmar baixa")
    if not pendentes:
        st.info("Não há contas pendentes disponíveis para baixa.")
        return

    opcoes = {
        f"#{conta[campo_id]} — {moeda(conta['valor'])}": conta[campo_id]
        for conta in pendentes
    }
    with st.form(f"form_baixa_{tipo}"):
        rotulo = st.selectbox("Selecione a conta", list(opcoes))
        confirmar = st.form_submit_button(
            "Confirmar pagamento" if pagar else "Confirmar recebimento",
            type="primary",
            use_container_width=True,
        )
    if confirmar:
        try:
            api.post(f"{endpoint}/{opcoes[rotulo]}/baixa")
            st.success("Baixa confirmada e fluxo de caixa atualizado.")
            st.rerun()
        except ApiError as erro:
            st.error(str(erro))


def pagina_compras(api: ApiClient) -> None:
    st.title("Compras")
    st.markdown(
        '<p class="app-subtitle">Cadastre o fornecedor, o pedido e a nota fiscal.</p>',
        unsafe_allow_html=True,
    )
    aba_fornecedor, aba_pedido, aba_nota = st.tabs(
        ["Fornecedor", "Pedido de compra", "Nota fiscal"]
    )

    with aba_fornecedor:
        with st.form("form_fornecedor", clear_on_submit=True):
            nome = st.text_input("Nome do fornecedor")
            cnpj = st.text_input("CNPJ")
            endereco = st.text_input("Endereço")
            telefone = st.text_input("Telefone")
            salvar_fornecedor = st.form_submit_button("Cadastrar fornecedor", type="primary")
        if salvar_fornecedor:
            if not all([nome.strip(), cnpj.strip(), endereco.strip(), telefone.strip()]):
                st.warning("Preencha todos os campos do fornecedor.")
            else:
                try:
                    api.post(
                        "/fornecedores/",
                        {
                            "nome": nome.strip(),
                            "cnpj": cnpj.strip(),
                            "endereco": endereco.strip(),
                            "telefone": telefone.strip(),
                        },
                    )
                    st.success("Fornecedor cadastrado.")
                    st.rerun()
                except ApiError as erro:
                    st.error(str(erro))

    try:
        fornecedores = api.get("/fornecedores/")
        unidades = api.get("/unidades/")
        produtos = api.get("/produtos/")
        pedidos = api.get("/compras/pedidos", params={"skip": 0, "limit": 500})
    except ApiError as erro:
        fornecedores, unidades, produtos, pedidos = [], [], [], []
        st.error(str(erro))

    with aba_fornecedor:
        if fornecedores:
            st.subheader("Fornecedores cadastrados")
            st.dataframe(
                preparar_tabela(
                    fornecedores,
                    {
                        "id": "ID",
                        "nome": "Nome",
                        "cnpj": "CNPJ",
                        "endereco": "Endereço",
                        "telefone": "Telefone",
                    },
                ),
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("Editar ou excluir fornecedor"):
                opcoes_edicao = {
                    f"#{item['id']} — {item['nome']}": item for item in fornecedores
                }
                rotulo_edicao = st.selectbox(
                    "Fornecedor", list(opcoes_edicao), key="fornecedor_edicao"
                )
                fornecedor_edicao = opcoes_edicao[rotulo_edicao]
                with st.form("form_editar_fornecedor"):
                    nome_edicao = st.text_input(
                        "Nome", value=fornecedor_edicao["nome"]
                    )
                    cnpj_edicao = st.text_input(
                        "CNPJ", value=fornecedor_edicao["cnpj"]
                    )
                    endereco_edicao = st.text_input(
                        "Endereço", value=fornecedor_edicao["endereco"]
                    )
                    telefone_edicao = st.text_input(
                        "Telefone", value=fornecedor_edicao["telefone"]
                    )
                    atualizar_fornecedor = st.form_submit_button("Salvar alterações")
                confirmar_exclusao = st.checkbox(
                    "Confirmo a exclusão deste fornecedor",
                    key="confirmar_exclusao_fornecedor",
                )
                excluir_fornecedor = st.button(
                    "Excluir fornecedor",
                    disabled=not confirmar_exclusao,
                    key="excluir_fornecedor",
                )
                if atualizar_fornecedor:
                    try:
                        api.put(
                            f"/fornecedores/{fornecedor_edicao['id']}",
                            {
                                "nome": nome_edicao,
                                "cnpj": cnpj_edicao,
                                "endereco": endereco_edicao,
                                "telefone": telefone_edicao,
                            },
                        )
                        st.success("Fornecedor atualizado.")
                        st.rerun()
                    except ApiError as erro:
                        st.error(str(erro))
                if excluir_fornecedor:
                    try:
                        api.delete(f"/fornecedores/{fornecedor_edicao['id']}")
                        st.success("Fornecedor excluído.")
                        st.rerun()
                    except ApiError as erro:
                        st.error(str(erro))

    with aba_pedido:
        if not fornecedores or not unidades or not produtos:
            st.info(
                "Cadastre fornecedor, unidade e produto antes de criar um pedido com estoque."
            )
        else:
            opcoes_fornecedor = {
                f"#{item['id']} — {item['nome']}": item["id"] for item in fornecedores
            }
            opcoes_unidade = {
                f"#{item['id_unidade']} — {item['nome']}": item["id_unidade"]
                for item in unidades
            }
            produtos_por_rotulo = {
                f"#{item['id_produto']} — {item['nome']}": item for item in produtos
            }
            fornecedor = st.selectbox("Fornecedor", list(opcoes_fornecedor))
            unidade = st.selectbox("Unidade de destino", list(opcoes_unidade))
            status_pedido = st.selectbox("Status inicial", ["pendente", "aprovado"])
            prazo = st.number_input(
                "Prazo de entrega (dias)", min_value=0, value=5, step=1
            )
            selecionados = st.multiselect(
                "Produtos do pedido", list(produtos_por_rotulo)
            )
            itens: list[dict] = []
            for rotulo in selecionados:
                produto = produtos_por_rotulo[rotulo]
                coluna_quantidade, coluna_preco = st.columns(2)
                quantidade = coluna_quantidade.number_input(
                    f"Quantidade — {produto['nome']}",
                    min_value=1,
                    value=1,
                    step=1,
                    key=f"compra_qtd_{produto['id_produto']}",
                )
                preco = coluna_preco.number_input(
                    f"Preço de compra — {produto['nome']}",
                    min_value=0.01,
                    value=float(produto["preco_venda"]),
                    step=0.01,
                    format="%.2f",
                    key=f"compra_preco_{produto['id_produto']}",
                )
                itens.append(
                    {
                        "id_produto": produto["id_produto"],
                        "quantidade": int(quantidade),
                        "preco_unitario": float(preco),
                    }
                )
            total_pedido = sum(
                item["quantidade"] * item["preco_unitario"] for item in itens
            )
            st.metric("Total estimado", moeda(total_pedido))
            salvar_pedido = st.button(
                "Criar pedido", type="primary", use_container_width=True
            )
            if salvar_pedido:
                if not itens:
                    st.warning("Selecione pelo menos um produto para o pedido.")
                    return
                try:
                    api.post(
                        "/compras/pedidos",
                        {
                            "id_fornecedor": opcoes_fornecedor[fornecedor],
                            "id_unidade": opcoes_unidade[unidade],
                            "status_pedido": status_pedido,
                            "prazo_entrega_dias": int(prazo),
                            "itens": itens,
                        },
                    )
                    st.success("Pedido de compra criado.")
                    st.rerun()
                except ApiError as erro:
                    st.error(str(erro))

        if pedidos:
            st.dataframe(
                preparar_tabela(
                    pedidos,
                    {
                        "id_pedido": "ID",
                        "id_fornecedor": "Fornecedor",
                        "id_unidade": "Unidade",
                        "data_pedido": "Data do pedido",
                        "status_pedido": "Status",
                        "prazo_entrega_dias": "Prazo (dias)",
                    },
                ),
                use_container_width=True,
                hide_index=True,
            )

    with aba_nota:
        pedidos_validos = [
            pedido
            for pedido in pedidos
            if pedido["status_pedido"] not in {"cancelado", "recebido"}
        ]
        if not pedidos_validos:
            st.info("Crie um pedido de compra antes de emitir a nota fiscal.")
        else:
            opcoes_pedido = {
                f"Pedido #{item['id_pedido']} — {item['status_pedido']}": item
                for item in pedidos_validos
            }
            with st.form("form_nota", clear_on_submit=True):
                pedido_rotulo = st.selectbox("Pedido de compra", list(opcoes_pedido))
                numero = st.text_input("Número da nota fiscal")
                pedido_escolhido = opcoes_pedido[pedido_rotulo]
                total_itens = sum(
                    item["quantidade"] * item["preco_unitario"]
                    for item in pedido_escolhido.get("itens", [])
                )
                valor_manual = None
                if total_itens:
                    st.info(f"Valor calculado pelos itens: {moeda(total_itens)}")
                else:
                    valor_manual = st.number_input(
                        "Valor total",
                        min_value=0.01,
                        value=100.0,
                        step=0.01,
                        format="%.2f",
                    )
                emitir_nota = st.form_submit_button("Emitir nota fiscal", type="primary")
            if emitir_nota:
                if not numero.strip():
                    st.warning("Informe o número da nota fiscal.")
                else:
                    try:
                        dados_nota: dict[str, object] = {
                            "id_pedido": pedido_escolhido["id_pedido"],
                            "numero_nota": numero.strip(),
                        }
                        if valor_manual is not None:
                            dados_nota["valor_total"] = float(valor_manual)
                        api.post("/compras/notas-fiscais", dados_nota)
                        st.success(
                            "Recebimento confirmado: estoque e conta a pagar atualizados."
                        )
                        st.rerun()
                    except ApiError as erro:
                        st.error(str(erro))


def pagina_produtos(api: ApiClient) -> None:
    st.title("Produtos")
    st.markdown(
        '<p class="app-subtitle">Cadastre categorias e produtos para vendas e estoque.</p>',
        unsafe_allow_html=True,
    )

    try:
        categorias = api.get("/categoria/")
        produtos = api.get("/produtos/")
    except ApiError as erro:
        st.error(str(erro))
        categorias, produtos = [], []

    aba_categoria, aba_produto = st.tabs(["Categoria", "Produto"])

    with aba_categoria:
        st.subheader("Cadastrar categoria")
        with st.form("form_categoria", clear_on_submit=True):
            nome_categoria = st.text_input("Nome da categoria")
            margem_lucro = st.number_input(
                "Margem de lucro (%)",
                min_value=0.0,
                value=20.0,
                step=0.5,
                format="%.2f",
            )
            salvar_categoria = st.form_submit_button(
                "Cadastrar categoria", type="primary"
            )

        if salvar_categoria:
            if not nome_categoria.strip():
                st.warning("Informe o nome da categoria.")
            else:
                try:
                    categoria = api.post(
                        "/categoria/",
                        {
                            "nome": nome_categoria.strip(),
                            "margem_lucro": float(margem_lucro),
                        },
                    )
                    st.success(
                        f"Categoria cadastrada com sucesso. ID: {categoria['id_categoria']}"
                    )
                    st.rerun()
                except ApiError as erro:
                    st.error(str(erro))

        if categorias:
            st.dataframe(
                preparar_tabela(
                    categorias,
                    {
                        "id_categoria": "ID",
                        "nome": "Nome",
                        "margem_lucro": "Margem (%)",
                    },
                ),
                use_container_width=True,
                hide_index=True,
            )
            with st.expander("Editar ou excluir categoria"):
                opcoes_edicao_categoria = {
                    f"#{item['id_categoria']} — {item['nome']}": item
                    for item in categorias
                }
                rotulo_categoria = st.selectbox(
                    "Categoria cadastrada",
                    list(opcoes_edicao_categoria),
                    key="categoria_edicao",
                )
                categoria_edicao = opcoes_edicao_categoria[rotulo_categoria]
                with st.form("form_editar_categoria"):
                    nome_categoria_edicao = st.text_input(
                        "Nome", value=categoria_edicao["nome"]
                    )
                    margem_categoria_edicao = st.number_input(
                        "Margem de lucro (%)",
                        min_value=0.0,
                        value=float(categoria_edicao.get("margem_lucro") or 0),
                        step=0.5,
                    )
                    atualizar_categoria = st.form_submit_button("Salvar alterações")
                confirmar_exclusao_categoria = st.checkbox(
                    "Confirmo a exclusão desta categoria",
                    key="confirmar_exclusao_categoria",
                )
                excluir_categoria = st.button(
                    "Excluir categoria",
                    disabled=not confirmar_exclusao_categoria,
                    key="excluir_categoria",
                )
                if atualizar_categoria:
                    try:
                        api.put(
                            f"/categoria/{categoria_edicao['id_categoria']}",
                            {
                                "nome": nome_categoria_edicao,
                                "margem_lucro": float(margem_categoria_edicao),
                            },
                        )
                        st.success("Categoria atualizada.")
                        st.rerun()
                    except ApiError as erro:
                        st.error(str(erro))
                if excluir_categoria:
                    try:
                        api.delete(f"/categoria/{categoria_edicao['id_categoria']}")
                        st.success("Categoria excluída.")
                        st.rerun()
                    except ApiError as erro:
                        st.error(str(erro))

    with aba_produto:
        st.subheader("Cadastrar produto")
        if not categorias:
            st.info("Cadastre uma categoria antes de cadastrar produtos.")
            return
        opcoes_categoria = {
            f"#{item['id_categoria']} — {item['nome']}": item["id_categoria"]
            for item in categorias
        }
        with st.form("form_produto", clear_on_submit=True):
            nome_produto = st.text_input("Nome do produto")
            categoria_selecionada = st.selectbox(
                "Categoria", list(opcoes_categoria)
            )
            codigo_barras = st.text_input("Código de barras")
            preco_venda = st.number_input(
                "Preço de venda",
                min_value=0.01,
                value=1.0,
                step=0.01,
                format="%.2f",
            )
            salvar_produto = st.form_submit_button("Cadastrar produto", type="primary")

        if salvar_produto:
            if not nome_produto.strip() or not codigo_barras.strip():
                st.warning("Preencha nome do produto e código de barras.")
            else:
                try:
                    api.post(
                        "/produtos/",
                        {
                            "nome": nome_produto.strip(),
                            "id_categoria": opcoes_categoria[categoria_selecionada],
                            "codigo_barras": codigo_barras.strip(),
                            "preco_venda": float(preco_venda),
                        },
                    )
                    st.success("Produto cadastrado com sucesso.")
                    st.rerun()
                except ApiError as erro:
                    st.error(str(erro))

        st.subheader("Produtos cadastrados")
        tabela = preparar_tabela(
            produtos,
            {
                "id_produto": "ID",
                "nome": "Nome",
                "id_categoria": "Categoria",
                "codigo_barras": "Código de barras",
                "preco_venda": "Valor",
            },
        )
        if tabela.empty:
            st.info("Nenhum produto cadastrado ainda.")
        else:
            st.dataframe(tabela, use_container_width=True, hide_index=True)
            with st.expander("Editar ou excluir produto"):
                opcoes_edicao_produto = {
                    f"#{item['id_produto']} — {item['nome']}": item
                    for item in produtos
                }
                rotulo_produto = st.selectbox(
                    "Produto cadastrado",
                    list(opcoes_edicao_produto),
                    key="produto_edicao",
                )
                produto_edicao = opcoes_edicao_produto[rotulo_produto]
                categorias_edicao = {
                    f"#{item['id_categoria']} — {item['nome']}": item["id_categoria"]
                    for item in categorias
                }
                ids_categorias = list(categorias_edicao.values())
                indice_categoria = ids_categorias.index(produto_edicao["id_categoria"])
                with st.form("form_editar_produto"):
                    nome_produto_edicao = st.text_input(
                        "Nome", value=produto_edicao["nome"]
                    )
                    categoria_produto_edicao = st.selectbox(
                        "Categoria",
                        list(categorias_edicao),
                        index=indice_categoria,
                    )
                    codigo_produto_edicao = st.text_input(
                        "Código de barras", value=produto_edicao["codigo_barras"]
                    )
                    preco_produto_edicao = st.number_input(
                        "Preço de venda",
                        min_value=0.01,
                        value=float(produto_edicao["preco_venda"]),
                        step=0.01,
                        format="%.2f",
                    )
                    atualizar_produto = st.form_submit_button("Salvar alterações")
                confirmar_exclusao_produto = st.checkbox(
                    "Confirmo a exclusão deste produto",
                    key="confirmar_exclusao_produto",
                )
                excluir_produto = st.button(
                    "Excluir produto",
                    disabled=not confirmar_exclusao_produto,
                    key="excluir_produto",
                )
                if atualizar_produto:
                    try:
                        api.put(
                            f"/produtos/{produto_edicao['id_produto']}",
                            {
                                "nome": nome_produto_edicao,
                                "id_categoria": categorias_edicao[
                                    categoria_produto_edicao
                                ],
                                "codigo_barras": codigo_produto_edicao,
                                "preco_venda": float(preco_produto_edicao),
                            },
                        )
                        st.success("Produto atualizado.")
                        st.rerun()
                    except ApiError as erro:
                        st.error(str(erro))
                if excluir_produto:
                    try:
                        api.delete(f"/produtos/{produto_edicao['id_produto']}")
                        st.success("Produto excluído.")
                        st.rerun()
                    except ApiError as erro:
                        st.error(str(erro))


def pagina_cadastros(api: ApiClient) -> None:
    st.title("Cadastros básicos")
    st.markdown(
        '<p class="app-subtitle">Unidades e clientes usados nos fluxos operacionais.</p>',
        unsafe_allow_html=True,
    )
    try:
        unidades = api.get("/unidades/")
        clientes = api.get("/clientes/")
    except ApiError as erro:
        st.error(str(erro))
        unidades, clientes = [], []

    aba_unidades, aba_clientes = st.tabs(["Unidades", "Clientes"])
    with aba_unidades:
        with st.form("form_unidade", clear_on_submit=True):
            nome_unidade = st.text_input("Nome da unidade")
            tipo_unidade = st.selectbox("Tipo", ["Loja", "CD"])
            salvar_unidade = st.form_submit_button(
                "Cadastrar unidade", type="primary"
            )
        if salvar_unidade:
            if not nome_unidade.strip():
                st.warning("Informe o nome da unidade.")
            else:
                try:
                    api.post(
                        "/unidades/",
                        {"nome": nome_unidade.strip(), "tipo": tipo_unidade},
                    )
                    st.success("Unidade cadastrada.")
                    st.rerun()
                except ApiError as erro:
                    st.error(str(erro))
        tabela_unidades = preparar_tabela(
            unidades,
            {"id_unidade": "ID", "nome": "Nome", "tipo": "Tipo"},
        )
        if tabela_unidades.empty:
            st.info("Nenhuma unidade cadastrada.")
        else:
            st.dataframe(tabela_unidades, use_container_width=True, hide_index=True)
            with st.expander("Editar ou excluir unidade"):
                opcoes_edicao_unidade = {
                    f"#{item['id_unidade']} — {item['nome']}": item
                    for item in unidades
                }
                rotulo_unidade = st.selectbox(
                    "Unidade cadastrada",
                    list(opcoes_edicao_unidade),
                    key="unidade_edicao",
                )
                unidade_edicao = opcoes_edicao_unidade[rotulo_unidade]
                tipos_unidade = ["Loja", "CD"]
                indice_tipo = (
                    tipos_unidade.index(unidade_edicao["tipo"])
                    if unidade_edicao["tipo"] in tipos_unidade
                    else 0
                )
                with st.form("form_editar_unidade"):
                    nome_unidade_edicao = st.text_input(
                        "Nome", value=unidade_edicao["nome"]
                    )
                    tipo_unidade_edicao = st.selectbox(
                        "Tipo", tipos_unidade, index=indice_tipo
                    )
                    atualizar_unidade = st.form_submit_button("Salvar alterações")
                confirmar_exclusao_unidade = st.checkbox(
                    "Confirmo a exclusão desta unidade",
                    key="confirmar_exclusao_unidade",
                )
                excluir_unidade = st.button(
                    "Excluir unidade",
                    disabled=not confirmar_exclusao_unidade,
                    key="excluir_unidade",
                )
                if atualizar_unidade:
                    try:
                        api.put(
                            f"/unidades/{unidade_edicao['id_unidade']}",
                            {
                                "nome": nome_unidade_edicao,
                                "tipo": tipo_unidade_edicao,
                            },
                        )
                        st.success("Unidade atualizada.")
                        st.rerun()
                    except ApiError as erro:
                        st.error(str(erro))
                if excluir_unidade:
                    try:
                        api.delete(f"/unidades/{unidade_edicao['id_unidade']}")
                        st.success("Unidade excluída.")
                        st.rerun()
                    except ApiError as erro:
                        st.error(str(erro))

    with aba_clientes:
        with st.form("form_cliente", clear_on_submit=True):
            nome_cliente = st.text_input("Nome do cliente")
            cpf_cliente = st.text_input("CPF")
            segmento = st.text_input("Segmento de marketing", value="geral")
            salvar_cliente = st.form_submit_button(
                "Cadastrar cliente", type="primary"
            )
        if salvar_cliente:
            if not nome_cliente.strip() or not cpf_cliente.strip():
                st.warning("Preencha nome e CPF.")
            else:
                try:
                    api.post(
                        "/clientes/",
                        {
                            "nome": nome_cliente.strip(),
                            "cpf": cpf_cliente.strip(),
                            "segmento_marketing": segmento.strip() or None,
                        },
                    )
                    st.success("Cliente cadastrado.")
                    st.rerun()
                except ApiError as erro:
                    st.error(str(erro))
        tabela_clientes = preparar_tabela(
            clientes,
            {
                "id_cliente": "ID",
                "nome": "Nome",
                "cpf": "CPF",
                "segmento_marketing": "Segmento",
            },
        )
        if tabela_clientes.empty:
            st.info("Nenhum cliente cadastrado.")
        else:
            st.dataframe(tabela_clientes, use_container_width=True, hide_index=True)
            with st.expander("Editar ou excluir cliente"):
                opcoes_edicao_cliente = {
                    f"#{item['id_cliente']} — {item['nome']}": item
                    for item in clientes
                }
                rotulo_cliente = st.selectbox(
                    "Cliente cadastrado",
                    list(opcoes_edicao_cliente),
                    key="cliente_edicao",
                )
                cliente_edicao = opcoes_edicao_cliente[rotulo_cliente]
                with st.form("form_editar_cliente"):
                    nome_cliente_edicao = st.text_input(
                        "Nome", value=cliente_edicao["nome"]
                    )
                    cpf_cliente_edicao = st.text_input(
                        "CPF", value=cliente_edicao["cpf"]
                    )
                    segmento_cliente_edicao = st.text_input(
                        "Segmento de marketing",
                        value=cliente_edicao.get("segmento_marketing") or "",
                    )
                    atualizar_cliente = st.form_submit_button("Salvar alterações")
                confirmar_exclusao_cliente = st.checkbox(
                    "Confirmo a exclusão deste cliente",
                    key="confirmar_exclusao_cliente",
                )
                excluir_cliente = st.button(
                    "Excluir cliente",
                    disabled=not confirmar_exclusao_cliente,
                    key="excluir_cliente",
                )
                if atualizar_cliente:
                    try:
                        api.put(
                            f"/clientes/{cliente_edicao['id_cliente']}",
                            {
                                "nome": nome_cliente_edicao,
                                "cpf": cpf_cliente_edicao,
                                "segmento_marketing": segmento_cliente_edicao or None,
                            },
                        )
                        st.success("Cliente atualizado.")
                        st.rerun()
                    except ApiError as erro:
                        st.error(str(erro))
                if excluir_cliente:
                    try:
                        api.delete(f"/clientes/{cliente_edicao['id_cliente']}")
                        st.success("Cliente excluído.")
                        st.rerun()
                    except ApiError as erro:
                        st.error(str(erro))


def pagina_vendas(api: ApiClient) -> None:
    st.title("Vendas")
    st.markdown(
        '<p class="app-subtitle">Registre itens, baixe o estoque e gere o recebível automaticamente.</p>',
        unsafe_allow_html=True,
    )
    try:
        unidades = api.get("/unidades/")
        clientes = api.get("/clientes/")
        produtos = api.get("/produtos/")
        vendas = api.get("/vendas/", params={"skip": 0, "limit": 200})
    except ApiError as erro:
        st.error(str(erro))
        return

    if not unidades or not produtos:
        st.info("Cadastre uma unidade e produtos antes de registrar vendas.")
        return

    opcoes_unidade = {
        f"#{item['id_unidade']} — {item['nome']}": item["id_unidade"]
        for item in unidades
    }
    opcoes_cliente = {"Venda sem cliente identificado": None}
    opcoes_cliente.update(
        {
            f"#{item['id_cliente']} — {item['nome']}": item["id_cliente"]
            for item in clientes
        }
    )
    produtos_por_rotulo = {
        f"#{item['id_produto']} — {item['nome']} ({moeda(item['preco_venda'])})": item
        for item in produtos
    }

    unidade = st.selectbox("Unidade da venda", list(opcoes_unidade))
    cliente = st.selectbox("Cliente", list(opcoes_cliente))
    forma_pagamento = st.selectbox(
        "Forma de pagamento",
        ["dinheiro", "pix", "cartao_debito", "cartao_credito", "boleto", "a_prazo"],
    )
    selecionados = st.multiselect("Produtos vendidos", list(produtos_por_rotulo))
    itens: list[dict] = []
    total = 0.0
    for rotulo in selecionados:
        produto = produtos_por_rotulo[rotulo]
        quantidade = st.number_input(
            f"Quantidade — {produto['nome']}",
            min_value=1,
            value=1,
            step=1,
            key=f"venda_qtd_{produto['id_produto']}",
        )
        itens.append(
            {"id_produto": produto["id_produto"], "quantidade": int(quantidade)}
        )
        total += float(produto["preco_venda"]) * int(quantidade)

    st.metric("Total da venda", moeda(total))
    if st.button("Finalizar venda", type="primary", use_container_width=True):
        if not itens:
            st.warning("Selecione pelo menos um produto.")
        else:
            try:
                api.post(
                    "/vendas/",
                    {
                        "id_unidade": opcoes_unidade[unidade],
                        "id_cliente": opcoes_cliente[cliente],
                        "forma_pagamento": forma_pagamento,
                        "itens": itens,
                    },
                )
                st.success("Venda registrada, estoque e financeiro atualizados.")
                st.rerun()
            except ApiError as erro:
                st.error(str(erro))

    st.subheader("Histórico de vendas")
    tabela_vendas = preparar_tabela(
        vendas,
        {
            "id_venda": "ID",
            "id_unidade": "Unidade",
            "id_usuario": "Usuário",
            "id_cliente": "Cliente",
            "data_hora": "Data",
            "valor_total": "Valor",
            "forma_pagamento": "Pagamento",
        },
    )
    if tabela_vendas.empty:
        st.info("Nenhuma venda registrada.")
    else:
        st.dataframe(tabela_vendas, use_container_width=True, hide_index=True)


def pagina_estoque(api: ApiClient) -> None:
    st.title("Estoque")
    st.markdown(
        '<p class="app-subtitle">Saldos por unidade e histórico rastreável de movimentações.</p>',
        unsafe_allow_html=True,
    )
    try:
        saldos = api.get("/estoque/saldos", params={"skip": 0, "limit": 500})
        movimentacoes = api.get(
            "/estoque/movimentacoes", params={"skip": 0, "limit": 200}
        )
        produtos = api.get("/produtos/")
        unidades = api.get("/unidades/")
    except ApiError as erro:
        st.error(str(erro))
        return

    nomes_produtos = {item["id_produto"]: item["nome"] for item in produtos}
    nomes_unidades = {item["id_unidade"]: item["nome"] for item in unidades}
    total_itens = sum(item["quantidade_atual"] for item in saldos)
    abaixo_minimo = sum(
        item["quantidade_atual"] <= item["estoque_minimo"] for item in saldos
    )
    coluna_total, coluna_alertas = st.columns(2)
    coluna_total.metric("Itens em estoque", total_itens)
    coluna_alertas.metric("Saldos no mínimo", abaixo_minimo)

    tabela_saldos = pd.DataFrame(saldos)
    if tabela_saldos.empty:
        st.info("O estoque ainda não possui saldo. Receba uma compra ou faça uma entrada manual.")
    else:
        tabela_saldos["Produto"] = tabela_saldos["id_produto"].map(nomes_produtos)
        tabela_saldos["Unidade"] = tabela_saldos["id_unidade"].map(nomes_unidades)
        tabela_saldos = tabela_saldos.rename(
            columns={
                "id_saldo": "ID",
                "quantidade_atual": "Quantidade",
                "estoque_minimo": "Mínimo",
            }
        )[["ID", "Produto", "Unidade", "Quantidade", "Mínimo"]]
        st.dataframe(tabela_saldos, use_container_width=True, hide_index=True)

    aba_movimento, aba_minimo = st.tabs(["Ajuste manual", "Estoque mínimo"])
    with aba_movimento:
        if not produtos or not unidades:
            st.info("Cadastre produtos e unidades antes de movimentar estoque.")
        else:
            opcoes_produto = {
                f"#{item['id_produto']} — {item['nome']}": item["id_produto"]
                for item in produtos
            }
            opcoes_unidade = {
                f"#{item['id_unidade']} — {item['nome']}": item["id_unidade"]
                for item in unidades
            }
            with st.form("form_movimento_estoque", clear_on_submit=True):
                produto = st.selectbox("Produto", list(opcoes_produto))
                unidade = st.selectbox("Unidade", list(opcoes_unidade))
                tipo = st.selectbox("Movimento", ["entrada", "saida", "perda"])
                quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)
                motivo = st.text_input("Motivo", value="Ajuste manual")
                movimentar = st.form_submit_button("Registrar movimento", type="primary")
            if movimentar:
                try:
                    api.post(
                        "/estoque/movimentacoes",
                        {
                            "id_produto": opcoes_produto[produto],
                            "id_unidade": opcoes_unidade[unidade],
                            "tipo_movimento": tipo,
                            "quantidade": int(quantidade),
                            "motivo": motivo.strip() or None,
                        },
                    )
                    st.success("Movimentação registrada.")
                    st.rerun()
                except ApiError as erro:
                    st.error(str(erro))

    with aba_minimo:
        if saldos:
            opcoes_saldo = {
                f"#{item['id_saldo']} — {nomes_produtos.get(item['id_produto'], item['id_produto'])} / {nomes_unidades.get(item['id_unidade'], item['id_unidade'])}": item
                for item in saldos
            }
            saldo_rotulo = st.selectbox("Saldo", list(opcoes_saldo))
            saldo_escolhido = opcoes_saldo[saldo_rotulo]
            minimo = st.number_input(
                "Novo estoque mínimo",
                min_value=0,
                value=int(saldo_escolhido["estoque_minimo"]),
                step=1,
            )
            if st.button("Atualizar mínimo"):
                try:
                    api.patch(
                        f"/estoque/saldos/{saldo_escolhido['id_saldo']}/minimo",
                        {"estoque_minimo": int(minimo)},
                    )
                    st.success("Estoque mínimo atualizado.")
                    st.rerun()
                except ApiError as erro:
                    st.error(str(erro))

    st.subheader("Últimas movimentações")
    tabela_movimentos = pd.DataFrame(movimentacoes)
    if not tabela_movimentos.empty:
        tabela_movimentos["Produto"] = tabela_movimentos["id_produto"].map(nomes_produtos)
        tabela_movimentos["Unidade"] = tabela_movimentos["id_unidade"].map(nomes_unidades)
        tabela_movimentos["Data"] = pd.to_datetime(
            tabela_movimentos["data_movimentacao"], errors="coerce"
        ).dt.strftime("%d/%m/%Y %H:%M")
        st.dataframe(
            tabela_movimentos.rename(
                columns={
                    "tipo_movimento": "Tipo",
                    "quantidade": "Quantidade",
                    "motivo": "Motivo",
                    "id_usuario": "Usuário",
                }
            )[["Data", "Produto", "Unidade", "Tipo", "Quantidade", "Motivo", "Usuário"]],
            use_container_width=True,
            hide_index=True,
        )


def garantir_estado_autenticacao() -> None:
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "usuario_logado" not in st.session_state:
        st.session_state.usuario_logado = None


def validar_sessao_ativa(api: ApiClient) -> None:
    if not st.session_state.access_token:
        return
    try:
        st.session_state.usuario_logado = api.get_me()
    except ApiError:
        st.session_state.access_token = None
        st.session_state.usuario_logado = None
        st.warning("Sessão expirada. Faça login novamente.")
        st.rerun()


def google_oidc_configurado() -> bool:
    try:
        return "auth" in st.secrets
    except Exception:
        return False


def sincronizar_login_google(api: ApiClient) -> None:
    if st.session_state.access_token:
        return
    usuario_google = getattr(st, "user", None)
    if not usuario_google or not getattr(usuario_google, "is_logged_in", False):
        return
    tokens = getattr(usuario_google, "tokens", None)
    token_id = None
    if tokens:
        token_id = getattr(tokens, "id", None)
        if token_id is None and hasattr(tokens, "get"):
            token_id = tokens.get("id")
    if not token_id:
        st.error(
            "O Google autenticou, mas o ID token não foi exposto. "
            "Adicione expose_tokens = [\"id\"] em .streamlit/secrets.toml."
        )
        return
    try:
        resposta = api.login_google(str(token_id))
        st.session_state.access_token = resposta["access_token"]
        st.rerun()
    except ApiError as erro:
        st.error(str(erro))


def renderizar_form_login(api: ApiClient) -> bool:
    with st.sidebar.form("form_login"):
        login = st.text_input("Login")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

    if not entrar:
        return False

    if not login.strip() or not senha:
        st.sidebar.warning("Informe login e senha.")
        return False

    try:
        resposta = api.login(login.strip(), senha)
        st.session_state.access_token = resposta["access_token"]
        st.success("Login realizado com sucesso.")
        st.rerun()
    except ApiError as erro:
        st.sidebar.error(str(erro))
    return False


def renderizar_form_cadastro(api: ApiClient) -> bool:
    with st.sidebar.form("form_cadastro"):
        nome = st.text_input("Nome")
        login = st.text_input("Login para acesso")
        senha = st.text_input("Senha", type="password")
        confirmar_senha = st.text_input("Confirmar senha", type="password")
        id_unidade_texto = st.text_input(
            "ID da unidade (opcional no primeiro cadastro)",
            help="No primeiro usuário, deixe vazio para criar a Unidade principal automaticamente.",
        )
        cadastrar = st.form_submit_button(
            "Cadastrar", type="primary", use_container_width=True
        )

    if not cadastrar:
        return False

    if not nome.strip() or not login.strip() or not senha:
        st.sidebar.warning("Preencha nome, login e senha.")
        return False

    if senha != confirmar_senha:
        st.sidebar.warning("A confirmação de senha não confere.")
        return False

    try:
        id_unidade = int(id_unidade_texto) if id_unidade_texto.strip() else None
    except ValueError:
        st.sidebar.warning("O ID da unidade deve ser um número inteiro.")
        return False

    try:
        api.register_user(
            nome=nome.strip(),
            login=login.strip(),
            senha=senha,
            id_unidade=id_unidade,
        )
        st.sidebar.success("Usuário cadastrado. Agora faça login.")
    except ApiError as erro:
        st.sidebar.error(str(erro))
    return False


def renderizar_usuario_logado() -> None:
    usuario = st.session_state.usuario_logado or {}
    nome_usuario = usuario.get("nome") or usuario.get("login") or "Usuário"
    st.sidebar.success(f"Conectado como {nome_usuario}")
    if st.sidebar.button("Sair", use_container_width=True):
        st.session_state.access_token = None
        st.session_state.usuario_logado = None
        usuario_google = getattr(st, "user", None)
        if usuario_google and getattr(usuario_google, "is_logged_in", False):
            st.logout()
        st.rerun()


def exibir_autenticacao(api_url: str) -> ApiClient | None:
    st.sidebar.subheader("Autenticação")
    api = ApiClient(api_url, access_token=st.session_state.access_token)

    sincronizar_login_google(api)
    validar_sessao_ativa(api)

    if not st.session_state.access_token:
        if google_oidc_configurado():
            st.sidebar.button(
                "Entrar com Google",
                on_click=st.login,
                use_container_width=True,
                type="primary",
            )
            st.sidebar.divider()
        acao = st.sidebar.radio("Acesso", ["Entrar", "Cadastrar"], key="acao_auth")
        if acao == "Entrar":
            renderizar_form_login(api)
        else:
            renderizar_form_cadastro(api)

        st.info("Faça login para acessar os módulos do SuperMais.")
        return None

    renderizar_usuario_logado()

    return ApiClient(api_url, access_token=st.session_state.access_token)


def main() -> None:
    garantir_estado_autenticacao()
    st.sidebar.title("SuperMais")
    st.sidebar.caption("ERP integrado")
    url_padrao = os.getenv("SUPERMAIS_API_URL", "http://127.0.0.1:8000")
    api_url = st.sidebar.text_input("Endereço da API", value=url_padrao)
    api = exibir_autenticacao(api_url)
    if not api:
        return

    pagina = st.sidebar.radio(
        "Navegação",
        [
            "Visão geral",
            "Cadastros",
            "Produtos",
            "Compras",
            "Vendas",
            "Estoque",
            "Contas a pagar",
            "Contas a receber",
        ],
    )

    if pagina == "Visão geral":
        pagina_visao_geral(api)
    elif pagina == "Cadastros":
        pagina_cadastros(api)
    elif pagina == "Produtos":
        pagina_produtos(api)
    elif pagina == "Compras":
        pagina_compras(api)
    elif pagina == "Vendas":
        pagina_vendas(api)
    elif pagina == "Estoque":
        pagina_estoque(api)
    elif pagina == "Contas a pagar":
        pagina_contas(api, "pagar")
    elif pagina == "Contas a receber":
        pagina_contas(api, "receber")


if __name__ == "__main__":
    main()
