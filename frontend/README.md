# Frontend SuperMais

Interface Streamlit integrada à API FastAPI do ERP SuperMais.

## Funcionalidades

- autenticação local e login Google opcional;
- visão geral financeira;
- cadastros de unidades, clientes, categorias, produtos e fornecedores;
- pedidos de compra e recebimento de notas fiscais;
- vendas integradas ao estoque e ao financeiro;
- saldos, estoque mínimo e movimentações;
- contas a pagar, contas a receber e fluxo de caixa.

## Executar

Com o PostgreSQL e a API FastAPI ativos, abra outro PowerShell na raiz do
repositório:

```powershell
cd C:\Users\Pichau\Documents\Super-Mais
.\backend\venv312\Scripts\Activate.ps1
pip install -r frontend\requirements.txt
python -m streamlit run frontend\app.py
```

A interface ficará disponível em `http://localhost:8501`. Por padrão, ela
acessa a API em `http://127.0.0.1:8000`. O endereço pode ser alterado na barra
lateral ou pela variável de ambiente `SUPERMAIS_API_URL`.

Para ativar o login Google, copie `.streamlit/secrets.toml.example` para
`.streamlit/secrets.toml` e preencha as credenciais OAuth. O arquivo real de
segredos não deve ser enviado ao Git.
