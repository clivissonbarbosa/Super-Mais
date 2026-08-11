# SuperMais

O SuperMais é um projeto de gestão financeira e operacional com uma API backend em FastAPI, um frontend em Streamlit e um banco de dados PostgreSQL. O sistema contempla módulos de cadastro, compras, estoque, financeiro e vendas, com foco em operações de supermercado/empresa comercial.

## Visão geral

- Backend: FastAPI + SQLAlchemy + Alembic
- Frontend: Streamlit
- Banco de dados: PostgreSQL
- Containerização: Docker Compose

## Estrutura do projeto

```text
backend/        # API FastAPI e modelos do banco
frontend/       # Interface Streamlit
docker-compose.yml
```

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- Python 3.10+ ou 3.12+
- pip
- Docker Desktop (para o PostgreSQL)
- Git

## 1. Subir o banco de dados

Na raiz do projeto, execute:

```powershell
docker compose up -d postgres
```

Isso irá iniciar um container PostgreSQL com:

- banco: `supermais`
- usuário: `supermais`
- senha: `supermais123`
- porta exposta: `5433`

Rodar banco populado:


- docker compose exec -T postgres psql -U supermais -d supermais < database.sql
## 2. Configurar e rodar o backend

Abra um terminal na pasta `backend` e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Se o ambiente for Linux/macOS, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Em seguida, aplique as migrações do banco:

```powershell
alembic upgrade head
```

Para iniciar a API:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API ficará disponível em:

- http://127.0.0.1:8000
- Documentação Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 3. Configurar e rodar o frontend

Em outro terminal, entre na pasta `frontend` e execute:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run app.py
```

A interface do Streamlit ficará disponível em:

- http://localhost:8501

## Variáveis de ambiente

O backend usa por padrão a seguinte URL de conexão:

```text
postgresql://supermais:supermais123@127.0.0.1:5433/supermais
```

Se necessário, você pode sobrescrever essa configuração através da variável `DATABASE_URL`.

O frontend pode acessar a API em `http://127.0.0.1:8000` por padrão. Caso queira apontar para outro endereço, ajuste a configuração da interface ou defina a variável `SUPERMAIS_API_URL`.

## Fluxos principais

O sistema já contempla operações como:

- cadastro e gestão de clientes, fornecedores, categorias e produtos;
- controle de compras e estoque;
- cadastro de contas a pagar e a receber;
- fluxo de caixa e financeiro;
- vendas e notas fiscais.

## Comandos úteis

Parar o banco:

```powershell
docker compose down
```

Recriar o banco do zero:

```powershell
docker compose down -v
docker compose up -d postgres
```
## Login

```
Senha: 12345678
login: clivisson1@gmail.com

```
## Observações

- Se a API não conectar ao PostgreSQL, verifique se o container está ativo com `docker compose ps`.
- Se houver erro nas migrações, repita o comando `alembic upgrade head` após conferir a conexão com o banco.
- Para desenvolvimento, a API pode ser reiniciada rapidamente com o modo `--reload` do Uvicorn.

