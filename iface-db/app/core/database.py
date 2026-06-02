from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.core.config import get_settings

settings = get_settings()

# 共用 engine pool（長期運行服務，避免每次請求建立/銷毀 engine）
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,         # 自動偵測斷線並重連
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    connect_args={"timeout": settings.DB_QUERY_TIMEOUT},  # pymssql per-command timeout
)


def get_session() -> Session:
    """取得 SQLAlchemy Session，供 FastAPI dependency 使用。"""
    return Session(engine)


def dispose_engine() -> None:
    """應用程式關閉時釋放 connection pool。"""
    engine.dispose()
