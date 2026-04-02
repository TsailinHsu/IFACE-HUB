"""
SP Query 端點
執行 Stored Procedure 並回傳結果集（tabular data）
適用情境：需要查詢 SP 回傳的列資料，而非僅執行（如 XXIF_RETEX_CM_AX_QUERY）
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.api.iface.deps import get_db
from app.api.iface.schemas import SpQueryRequest, QueryResponse
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post(
    "/{procedure_name}",
    response_model=QueryResponse,
    summary="執行 SP 並回傳結果集（tabular rows）",
)
def run_sp_query(
    procedure_name: str,
    payload: SpQueryRequest,
    db: Annotated[Session, Depends(get_db)],
) -> QueryResponse:
    """
    執行 config.ALLOWED_SP_QUERIES 白名單中的 Stored Procedure，
    並將回傳的結果集序列化為 list[dict] 回傳。

    白名單機制防止任意 SP 被呼叫。
    """
    if procedure_name not in settings.ALLOWED_SP_QUERIES:
        raise HTTPException(
            status_code=403,
            detail=f"不允許的 SP 查詢: {procedure_name}",
        )

    sp_def = settings.ALLOWED_SP_QUERIES[procedure_name]
    database = sp_def["database"]

    sql_parts = [f"EXECUTE {procedure_name}"]
    if payload.params:
        param_clauses = [f"@{k} = :{k}" for k in payload.params]
        sql_parts.append(", ".join(param_clauses))
    sql = text(" ".join(sql_parts))

    try:
        if database != settings.IFACE_DB:
            _s = settings
            alt_url = (
                f"mssql+pymssql://{_s.IFACE_USER}:{_s.IFACE_PWD}"
                f"@{_s.IFACE_SERVER}/{database}"
            )
            alt_engine = create_engine(alt_url, pool_pre_ping=True)
            try:
                with Session(alt_engine) as alt_session:
                    result = alt_session.execute(sql, payload.params or {})
                    columns = list(result.keys())
                    rows = [dict(zip(columns, row)) for row in result.fetchall()]
            finally:
                alt_engine.dispose()
        else:
            result = db.execute(sql, payload.params or {})
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SP 查詢 {procedure_name} 失敗: {e}",
        ) from e

    return QueryResponse(status="success", data=rows)
