from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.iface.deps import get_db
from app.api.iface.schemas import StatusUpdateRequest, StatusUpdateResponse

router = APIRouter()


@router.post(
    "/",
    response_model=StatusUpdateResponse,
    summary="更新 IFACE 資料狀態（對應 ifaceStatusUpdate）",
)
def update_status(
    payload: StatusUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> StatusUpdateResponse:
    """
    依 APP_MODULE + APP_FUNCTION + STATUS 批次更新 IFACE 資料列的狀態。

    一般使用情境：
      '0' → '5'  fetcher 呼叫 SP 前標記為處理中
      '5' → '6'  SP 執行完成後標記為完成
      '5' → 'E'  SP 執行失敗後標記為錯誤
    """
    set_processed = payload.status_to in ("6", "E")
    sql = text("""
        UPDATE IFACE
        SET STATUS         = :status_to,
            PROCESSED_DATE = CASE WHEN :set_processed = 1 THEN SYSUTCDATETIME() ELSE PROCESSED_DATE END
        WHERE APP_MODULE   = :module
          AND APP_FUNCTION = :function
          AND STATUS       = :status_from
    """)

    params = {
        "status_to":     payload.status_to,
        "set_processed": 1 if set_processed else 0,
        "module":        payload.module,
        "function":      payload.function,
        "status_from":   payload.status_from,
    }

    try:
        result = db.execute(sql, params)
        db.commit()
        rows_affected = result.rowcount
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"狀態更新失敗: {e}") from e

    return StatusUpdateResponse(status="success", rows_affected=rows_affected)
