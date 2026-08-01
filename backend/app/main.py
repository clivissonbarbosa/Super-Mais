from fastapi import FastAPI
from app.database import Base, engine
from app.models import produto
from app.routes import produto as produto_router
from sqlalchemy import text
from app.models import User
from app.routes import user as user_router
from app.routes import fornecedor as fornecedor_router
app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(produto_router.router)
app.include_router(user_router.router)
app.include_router(fornecedor_router.router)

@app.get("/")
def home():
    return {"status": "funcionando"}

@app.get("/testar-banco")
def testar_banco():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"banco": "conectado com sucesso"}