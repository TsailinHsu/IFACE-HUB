from typing import Any
from pydantic import BaseModel, field_validator


class TransactionCreate(BaseModel):
    """
    對應 ifaceUtil.ifaceImport() 的參數。
    json_doc 接受 dict 或 list，寫入前序列化為 JSON 字串。
    """
    api_url:        str
    json_doc:       dict | list
    query:          dict | list | None = None
    module:         str
    function:       str
    merchant:       dict | list | None = None
    initial_status: str = "0"

    @field_validator("initial_status")
    @classmethod
    def single_char(cls, v: str) -> str:
        if len(v) != 1:
            raise ValueError("initial_status 必須為單一字元")
        return v


class TransactionResponse(BaseModel):
    status:   str
    batch_id: str


class StatusUpdateRequest(BaseModel):
    """
    對應 ifaceUtil.ifaceStatusUpdate() 的參數。
    status_from / status_to 為單一字元字串。
    """
    module:      str
    function:    str
    status_from: str
    status_to:   str

    @field_validator("status_from", "status_to")
    @classmethod
    def single_char(cls, v: str) -> str:
        if len(v) != 1:
            raise ValueError("status 必須為單一字元")
        return v


class StatusUpdateResponse(BaseModel):
    status:        str
    rows_affected: int


class ProcedureRequest(BaseModel):
    """
    對應 databaseUtil.runProcedure() 的參數。
    database 預設為 IFACE，可指定其他資料庫（如 SR）。
    params 為選用的 SP 參數字典。
    """
    database: str = "IFACE"
    params:   dict[str, Any] | None = None


class ProcedureResponse(BaseModel):
    status:         str
    procedure_name: str
    database:       str


class QueryResponse(BaseModel):
    status: str
    data:   Any


class SpQueryRequest(BaseModel):
    """
    SP Query 端點的參數：僅需 SP 的具名參數（選用）。
    """
    params: dict[str, Any] | None = None
