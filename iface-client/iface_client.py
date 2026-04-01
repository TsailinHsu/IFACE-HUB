"""
iface-db HTTP 客戶端
所有 fetcher 共用相同介面，各自透過 DB_API_URL 環境變數指向對應的 iface-db 實例
"""

import os
import requests

_BASE_URL = os.getenv("DB_API_URL", "http://iface-db:8000").rstrip("/")
_TIMEOUT_SHORT = 30   # 寫入 / 狀態更新
_TIMEOUT_LONG  = 120  # SP 執行（部分 SP 處理量大）


def iface_import(api_url: str, json_doc: dict | list, query: dict | None,
                 module: str, function: str, merchant: dict | None = None,
                 initial_status: str = "0") -> str:
    """
    寫入 IFACE 資料，回傳 BATCH_ID。
    對應 ifaceUtil.ifaceImport()。
    initial_status: 初始 STATUS 值，預設 '0'（待 SP 處理）；
                    無需匯入 ERP 時可傳 '6'（已完成）。
    """
    payload = {
        "api_url":        api_url,
        "json_doc":       json_doc,
        "query":          query or {},
        "module":         module,
        "function":       function,
        "merchant":       merchant or {},
        "initial_status": initial_status,
    }
    resp = requests.post(
        f"{_BASE_URL}/api/v1/iface/transactions/",
        json=payload,
        timeout=_TIMEOUT_SHORT,
    )
    resp.raise_for_status()
    return resp.json()["batch_id"]


def run_procedure(procedure_name: str, database: str = "IFACE",
                  params: dict | None = None) -> None:
    """
    執行 MSSQL Stored Procedure。
    對應 databaseUtil.runProcedure()。
    """
    payload = {"database": database, "params": params or {}}
    resp = requests.post(
        f"{_BASE_URL}/api/v1/iface/sp/{procedure_name}",
        json=payload,
        timeout=_TIMEOUT_LONG,
    )
    resp.raise_for_status()


def status_update(module: str, function: str,
                  status_from: str, status_to: str) -> int:
    """
    更新 IFACE 資料狀態，回傳影響筆數。
    對應 ifaceUtil.ifaceStatusUpdate()。
    """
    payload = {
        "module":      module,
        "function":    function,
        "status_from": status_from,
        "status_to":   status_to,
    }
    resp = requests.post(
        f"{_BASE_URL}/api/v1/iface/status-update/",
        json=payload,
        timeout=_TIMEOUT_SHORT,
    )
    resp.raise_for_status()
    return resp.json().get("rows_affected", 0)


def get_reply(view_name: str) -> list:
    """
    查詢 Reply View，回傳資料列表。
    對應 databaseUtil.databaseQuery() 的 reply 查詢。
    """
    resp = requests.get(
        f"{_BASE_URL}/api/v1/iface/reply/{view_name}",
        timeout=_TIMEOUT_SHORT,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def named_query(query_name: str, **kwargs) -> dict:
    """
    執行具名查詢（帶參數的 MSSQL 查詢）。
    主要用途：RETEX CM 採購單回傳 POS 的前置查詢。
    """
    resp = requests.get(
        f"{_BASE_URL}/api/v1/iface/named-query/{query_name}",
        params=kwargs,
        timeout=_TIMEOUT_SHORT,
    )
    resp.raise_for_status()
    return resp.json().get("data", {})


def query_view(view_name: str, module: str | None = None,
               function: str | None = None) -> list:
    """
    查詢參考資料 View（如 XX_DATASTAMP）。
    """
    params: dict = {}
    if module:
        params["module"] = module
    if function:
        params["function"] = function

    resp = requests.get(
        f"{_BASE_URL}/api/v1/iface/query/{view_name}",
        params=params,
        timeout=_TIMEOUT_SHORT,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])
