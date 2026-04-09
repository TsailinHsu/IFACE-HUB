import json
import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.iface.deps import get_db
from app.api.iface.schemas import TransactionCreate, TransactionResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def _make_batch_id() -> str:
    """BATCH_ID 格式與現有 ifaceUtil 一致：%Y%j%H%M%S%f"""
    return datetime.strftime(datetime.now(), "%Y%j%H%M%S%f")


@router.post(
    "/",
    response_model=TransactionResponse,
    status_code=201,
    summary="寫入 IFACE 資料（對應 ifaceImport）",
)
def create_transaction(
    payload: TransactionCreate,
    db: Annotated[Session, Depends(get_db)],
) -> TransactionResponse:
    """
    將外部 API 回應寫入 IFACE 資料表。
    initial_status='0'（預設）：等待 SP 處理，PROCESSED_DATE 留空。
    initial_status='6'：無資料需匯入，直接標記完成並填入 PROCESSED_DATE。
    回傳 BATCH_ID 供後續追蹤。
    """
    batch_id = _make_batch_id()
    now = datetime.now()
    is_terminal = payload.initial_status not in ("0", "5")

    sql = text("""
        INSERT INTO IFACE
            (BATCH_ID, CREATION_DATE, PROCESSED_DATE, API, APP_MODULE, APP_FUNCTION,
             STATUS, JSON_DOC, QUERY_PARAMS, MERCHANT, RETRY_COUNT)
        VALUES
            (:batch_id, :creation_date, :processed_date, :api, :module, :function,
             :status, :json_doc, :query, :merchant, 0)
    """)

    params = {
        "batch_id":       batch_id,
        "creation_date":  now,
        "processed_date": now if is_terminal else None,
        "api":            payload.api_url,
        "module":         payload.module,
        "function":       payload.function,
        "status":         payload.initial_status,
        "json_doc":       json.dumps(payload.json_doc, ensure_ascii=False),
        "query":          json.dumps(payload.query,    ensure_ascii=False) if payload.query    is not None else None,
        "merchant":       json.dumps(payload.merchant, ensure_ascii=False) if payload.merchant is not None else None,
    }

    try:
        db.execute(sql, params)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception("寫入 IFACE 失敗")
        raise HTTPException(status_code=500, detail=f"寫入 IFACE 失敗: {e}") from e

    return TransactionResponse(status="success", batch_id=batch_id)
