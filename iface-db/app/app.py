from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import dispose_engine
from app.api.iface.routes import transactions, status_update, procedures, reply, query, named_query


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup：engine pool 在 database.py import 時已初始化
    yield
    # shutdown：釋放 connection pool
    dispose_engine()


app = FastAPI(
    title="iface-db API",
    description="IFACE MSSQL 資料庫操作 API，供各 fetcher 容器呼叫",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(
    transactions.router,
    prefix="/api/v1/iface/transactions",
    tags=["transactions"],
)
app.include_router(
    status_update.router,
    prefix="/api/v1/iface/status-update",
    tags=["status"],
)
app.include_router(
    procedures.router,
    prefix="/api/v1/iface/sp",
    tags=["procedures"],
)
app.include_router(
    reply.router,
    prefix="/api/v1/iface/reply",
    tags=["reply"],
)
app.include_router(
    query.router,
    prefix="/api/v1/iface/query",
    tags=["query"],
)
app.include_router(
    named_query.router,
    prefix="/api/v1/iface/named-query",
    tags=["named-query"],
)


@app.get("/", tags=["health"])
def root():
    return {"service": "iface-db API", "status": "running"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
