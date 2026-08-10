from fastapi import FastAPI
from app.database import Base, engine

from app.models import (
    Categoria,
    Cliente,
    Conta_Pagar,
    Conta_Receber,
    Fluxo_Caixa,
    Fornecedor,
    Nota_Fiscal,
    Pedido_Compra,
    Unidade,
    User,
    Vendas,
    produto,
)

from app.routes import categoria as categoria_router
from app.routes import produto as produto_router
from sqlalchemy import text
from app.routes import user as user_router
from app.routes import fornecedor as fornecedor_router
from app.routes import vendas as vendas_router
from app.routes import unidade as unidade_router
from app.routes import cliente as cliente_router
from app.routes import compras as compras_router
from app.routes import financeiro as financeiro_router
app = FastAPI()

#Base.metadata.create_all(bind=engine)

app.include_router(categoria_router.router)
app.include_router(produto_router.router)
app.include_router(user_router.router)
app.include_router(fornecedor_router.router)
app.include_router(vendas_router.router)
app.include_router(unidade_router.router)
app.include_router(cliente_router.router)
app.include_router(compras_router.router)
app.include_router(financeiro_router.router)
@app.get("/")
def home():
    return {"status": "funcionando"}

@app.get("/testar-banco")
def testar_banco():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"banco": "conectado com sucesso"}
