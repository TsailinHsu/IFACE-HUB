from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.iface.deps import get_db
from app.api.iface.schemas import ProcedureRequest, ProcedureResponse
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post(
    "/{procedure_name}",
    response_model=ProcedureResponse,
    summary="執行 MSSQL Stored Procedure（對應 runProcedure）",
)
def run_procedure(
    procedure_name: str,
    payload: ProcedureRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ProcedureResponse:
    """
    執行指定的 MSSQL Stored Procedure。

    - procedure_name：SP 名稱，限白名單內的 SP（config.ALLOWED_PROCEDURES）
    - database：目標資料庫，預設 IFACE，可指定 SR 等其他資料庫
    - params：SP 的具名參數，選用

    白名單機制防止任意 SQL 物件執行。
    """
    if procedure_name not in settings.ALLOWED_PROCEDURES:
        raise HTTPException(
            status_code=403,
            detail=f"不允許執行的 stored procedure: {procedure_name}",
        )

    # 建立 EXECUTE 語句，含具名參數
    sql_parts = [f"EXECUTE {procedure_name}"]
    if payload.params:
        param_clauses = [f"@{k} = :{k}" for k in payload.params]
        sql_parts.append(", ".join(param_clauses))

    sql = text(" ".join(sql_parts))

    try:
        db.execute(sql, payload.params or {})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"執行 {procedure_name} 失敗: {e}",
        ) from e

    return ProcedureResponse(
        status="success",
        procedure_name=procedure_name,
        database=payload.database,
    )
