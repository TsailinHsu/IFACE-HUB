import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.iface.deps import get_db
from app.api.iface.schemas import QueryResponse
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get(
    "/{view_name}",
    response_model=QueryResponse,
    summary="一般查詢（XX_DATASTAMP 等參考資料 view）",
)
def query_view(
    view_name: str,
    db: Annotated[Session, Depends(get_db)],
    module: str | None = Query(default=None, description="APP_MODULE 過濾"),
    function: str | None = Query(default=None, description="APP_FUNCTION 過濾"),
) -> QueryResponse:
    """
    查詢參考資料 view，主要用途：
      - XX_DATASTAMP：RETEX fetcher 取得最新 DataStamp
      - 其他輔助查詢

    支援選用的 module / function 查詢參數，由 view 決定是否使用。
    限白名單內的 view（config.ALLOWED_VIEWS）。
    """
    if view_name not in settings.ALLOWED_VIEWS:
        raise HTTPException(
            status_code=403,
            detail=f"不允許查詢的 view: {view_name}",
        )

    params: dict[str, str] = {}
    where_clauses: list[str] = []

    if module:
        where_clauses.append("APP_MODULE = :module")
        params["module"] = module
    if function:
        where_clauses.append("APP_FUNCTION = :function")
        params["function"] = function

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    sql = text(
        f"SELECT * FROM {view_name} {where_sql} FOR JSON PATH, ROOT('Result')"
    )

    try:
        result = db.execute(sql, params).scalar_one_or_none()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查詢 {view_name} 失敗: {e}",
        ) from e

    data: Any = json.loads(result)["Result"] if result else []

    return QueryResponse(status="success", data=data)
