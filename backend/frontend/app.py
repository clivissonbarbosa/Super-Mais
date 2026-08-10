import os
from datetime import date, datetime, time

import pandas as pd
import streamlit as st

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
    for coluna in ["Vencimento", "Confirmação", "Emissão", "Data do pedido"]:
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
                except ApiError as erro:
                    st.error(str(erro))

    try:
        fornecedores = api.get("/fornecedores/")
        pedidos = api.get("/compras/pedidos", params={"skip": 0, "limit": 500})
    except ApiError as erro:
        fornecedores, pedidos = [], []
        st.error(str(erro))

    with aba_pedido:
        if not fornecedores:
            st.info("Cadastre pelo menos um fornecedor antes de criar o pedido.")
        else:
            opcoes_fornecedor = {
                f"#{item['id']} — {item['nome']}": item["id"] for item in fornecedores
            }
            with st.form("form_pedido", clear_on_submit=True):
                fornecedor = st.selectbox("Fornecedor", list(opcoes_fornecedor))
                status_pedido = st.selectbox(
                    "Status inicial", ["pendente", "aprovado", "recebido"]
                )
                prazo = st.number_input(
                    "Prazo de entrega (dias)", min_value=0, value=5, step=1
                )
                salvar_pedido = st.form_submit_button("Criar pedido", type="primary")
            if salvar_pedido:
                try:
                    api.post(
                        "/compras/pedidos",
                        {
                            "id_fornecedor": opcoes_fornecedor[fornecedor],
                            "status_pedido": status_pedido,
                            "prazo_entrega_dias": int(prazo),
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
                        "data_pedido": "Data do pedido",
                        "status_pedido": "Status",
                        "prazo_entrega_dias": "Prazo (dias)",
                    },
                ),
                use_container_width=True,
                hide_index=True,
            )

    with aba_nota:
        pedidos_validos = [pedido for pedido in pedidos if pedido["status_pedido"] != "cancelado"]
        if not pedidos_validos:
            st.info("Crie um pedido de compra antes de emitir a nota fiscal.")
        else:
            opcoes_pedido = {
                f"Pedido #{pedido['id_pedido']} — {pedido['status_pedido']}": pedido["id_pedido"]
                for pedido in pedidos_validos
            }
            with st.form("form_nota", clear_on_submit=True):
                pedido = st.selectbox("Pedido de compra", list(opcoes_pedido))
                numero = st.text_input("Número da nota fiscal")
                valor = st.number_input(
                    "Valor total", min_value=0.01, value=100.0, step=0.01, format="%.2f"
                )
                emitir_nota = st.form_submit_button("Emitir nota fiscal", type="primary")
            if emitir_nota:
                if not numero.strip():
                    st.warning("Informe o número da nota fiscal.")
                else:
                    try:
                        api.post(
                            "/compras/notas-fiscais",
                            {
                                "id_pedido": opcoes_pedido[pedido],
                                "numero_nota": numero.strip(),
                                "valor_total": float(valor),
                            },
                        )
                        st.success("Nota emitida e conta a pagar criada automaticamente.")
                        st.rerun()
                    except ApiError as erro:
                        st.error(str(erro))


def main() -> None:
    st.sidebar.title("SuperMais")
    st.sidebar.caption("Módulo financeiro")
    url_padrao = os.getenv("SUPERMAIS_API_URL", "http://127.0.0.1:8000")
    api_url = st.sidebar.text_input("Endereço da API", value=url_padrao)
    pagina = st.sidebar.radio(
        "Navegação",
        ["Visão geral", "Contas a pagar", "Contas a receber", "Compras"],
    )
    st.sidebar.divider()
    st.sidebar.info("Autenticação e vendas serão integradas após o merge do módulo de login.")

    api = ApiClient(api_url)
    if pagina == "Visão geral":
        pagina_visao_geral(api)
    elif pagina == "Contas a pagar":
        pagina_contas(api, "pagar")
    elif pagina == "Contas a receber":
        pagina_contas(api, "receber")
    else:
        pagina_compras(api)


if __name__ == "__main__":
    main()
