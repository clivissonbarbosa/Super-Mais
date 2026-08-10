# Frontend financeiro

Interface Streamlit simples para consumir a API da SuperMais. As telas disponíveis são:

- visão geral financeira;
- contas a pagar e confirmação de pagamento;
- contas a receber e confirmação de recebimento;
- cadastro de fornecedor, pedido de compra e nota fiscal.

## Executar

Com o PostgreSQL e a API FastAPI ativos, abra outro terminal na pasta `backend`:

```powershell
.\venv312\Scripts\Activate.ps1
pip install -r frontend/requirements.txt
python -m streamlit run frontend/app.py
```

A interface fica disponível em `http://localhost:8501`. Por padrão ela acessa a API em `http://127.0.0.1:8000`; o endereço pode ser alterado na barra lateral ou pela variável `SUPERMAIS_API_URL`.

O módulo de vendas será adicionado depois da integração com a autenticação, para que o usuário da operação venha da sessão autenticada.
