"""
Named Query 端點
處理需要帶參數查詢 MSSQL 但無法用 View 表達的情境
主要用途：RETEX CM 採購單查詢（retexDocUpdate 流程）
"""

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.iface.deps import get_db
from app.api.iface.schemas import QueryResponse
from app.core.config import get_settings
from app.core.database import engine

router = APIRouter()
settings = get_settings()


@router.get(
    "/{query_name}",
    response_model=QueryResponse,
    summary="執行具名查詢（帶參數的 MSSQL 查詢，如 RETEX CM 訂單回傳）",
)
def run_named_query(
    query_name: str,
    db: Annotated[Session, Depends(get_db)],
    create_date: str | None = Query(default=None, description="YYYYMMDD 格式"),
) -> QueryResponse:
    """
    執行 config.NAMED_QUERIES 中定義的具名 SQL 查詢。

    支援的查詢：
      - RETEX_CM_GET_ORDERS       (create_date 必填)
      - RETEX_CM_A000_GET_ORDERS  (不需參數，讀取 IFACE STATUS='0' 的 CM 資料)
    """
    if query_name not in settings.NAMED_QUERIES:
        raise HTTPException(
            status_code=403,
            detail=f"不支援的具名查詢: {query_name}",
        )

    query_def = settings.NAMED_QUERIES[query_name]
    sql_str   = query_def["sql"]
    database  = query_def["database"]

    # 組合查詢參數
    params: dict[str, Any] = {}
    if create_date:
        params["create_date"] = create_date

    # 若需要使用不同 database，建立對應 engine 連線
    # 目前 RETEX_CM_GET_ORDERS 需連 SR，RETEX_CM_A000_GET_ORDERS 連 IFACE（預設）
    if database != settings.IFACE_DB:
        from sqlalchemy import create_engine
        from app.core.config import get_settings as _gs

        _s = _gs()
        alt_url = (
            f"mssql+pymssql://{_s.IFACE_USER}:{_s.IFACE_PWD}"
            f"@{_s.IFACE_SERVER}/{database}"
        )
        alt_engine = create_engine(alt_url, pool_pre_ping=True)
        try:
            with Session(alt_engine) as alt_session:
                result = alt_session.execute(text(sql_str), params).scalar_one_or_none()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"具名查詢 {query_name} 失敗: {e}",
            ) from e
        finally:
            alt_engine.dispose()
    else:
        try:
            result = db.execute(text(sql_str), params).scalar_one_or_none()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"具名查詢 {query_name} 失敗: {e}",
            ) from e

    data: Any = json.loads(result) if result else {}

    return QueryResponse(status="success", data=data)
