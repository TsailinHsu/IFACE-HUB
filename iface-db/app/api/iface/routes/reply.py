import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
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
    summary="查詢 Reply View（對應 EIP/xdelivery 回寫所需資料）",
)
def get_reply(
    view_name: str,
    db: Annotated[Session, Depends(get_db)],
) -> QueryResponse:
    """
    查詢指定的 MSSQL View，回傳 JSON 結果供 fetcher 回寫外部 API。

    View 需以 FOR JSON PATH, ROOT('Result') 結尾，
    或回傳可直接序列化的結果集。

    限白名單內的 view（config.ALLOWED_VIEWS）。
    """
    if view_name not in settings.ALLOWED_VIEWS:
        raise HTTPException(
            status_code=403,
            detail=f"不允許查詢的 view: {view_name}",
        )

    sql = text(f"SELECT * FROM {view_name} FOR JSON PATH, ROOT('Result')")

    try:
        # MSSQL FOR JSON 結果可能被切成多列（每列最多 2033 字元），需串接後再解析
        rows = db.execute(sql).scalars().all()
        result = "".join(r for r in rows if r) if rows else None
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查詢 {view_name} 失敗: {e}",
        ) from e

    data: Any = json.loads(result)["Result"] if result else []

    return QueryResponse(status="success", data=data)
