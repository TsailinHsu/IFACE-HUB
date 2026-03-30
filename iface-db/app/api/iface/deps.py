from typing import Generator
from sqlalchemy.orm import Session
from app.core.database import get_session


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency：提供 DB Session，請求結束後自動關閉。"""
    session = get_session()
    try:
        yield session
    finally:
        session.close()
