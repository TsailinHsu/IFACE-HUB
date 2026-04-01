"""
RETEX POS API 客戶端
封裝 AES-256 加密認證及所有對 pos.speeding-rocket.io 的 HTTP 請求
"""

import json
import os
import requests
from datetime import datetime

from codex import getTimeStamp, createCipherText, createSignature, decryptBase64, decryptAES256
from iface_client import iface_import

_BASE_URL   = os.getenv("RETEX_BASE_URL", "http://pos.speeding-rocket.io:82")
_TOKEN      = os.getenv("RETEX_TOKEN",    "")
_API_KEY    = os.getenv("RETEX_API_KEY",  "")
_API_IV     = os.getenv("RETEX_API_IV",   "")
_SALT_KEY   = os.getenv("RETEX_SALT_KEY", "")

# API 路徑
_POS_DOC_QUERY      = "/Vip/PosDocQuery"
_POS_SALES_DOC      = "/Vip/PosSalesDocQuery"
_ERP_DOC_UPDATE     = "/Vip/ErpDocUpdate"


def _call_api(api_url: str, request_data: dict) -> dict:
    """呼叫 RETEX API（AES-256 加密 + SHA-512 簽章）。"""
    time_stamp   = getTimeStamp(datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"))
    cipher_data  = createCipherText(
        json.dumps(request_data, ensure_ascii=False), _API_KEY, _API_IV
    ).decode("UTF-8")
    signature = createSignature(str(time_stamp), _TOKEN, _SALT_KEY, cipher_data)

    headers = {
        "Content-Type": "Application/JSON; Charset=utf8",
        "ts":           str(time_stamp),
        "t":            _TOKEN,
        "s":            signature,
    }

    try:
        resp = requests.post(api_url, headers=headers, json=request_data, timeout=60)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    fetched      = json.loads(resp.text)
    response_enc = fetched["ResponseData"]
    decrypted    = decryptAES256(
        decryptBase64(response_enc), decryptBase64(_API_KEY), decryptBase64(_API_IV)
    )
    return json.loads(decrypted.decode("UTF-8"))


def _query_and_import(api_url: str, request_data: dict, doc_type: str) -> None:
    """查詢 RETEX API 並將結果寫入 IFACE。
    無論有無資料皆寫入，ResultNo != '00' 時以 STATUS='6' 標記已完成（不需匯入 ERP）。
    """
    json_data = _call_api(api_url, request_data)
    if json_data.get("ResultNo") == "00":
        iface_import(api_url, json_data, request_data, "RETEX", doc_type)
    else:
        iface_import(api_url, json_data, request_data, "RETEX", doc_type, initial_status="6")


# ---------------------------------------------------------------------------
# Fetch functions
# ---------------------------------------------------------------------------

def query_docs(request_data: dict, doc_type: str) -> None:
    """查詢 POS 單據（PO/CM/ST/BO/MO/MI/ME）並寫入 IFACE。"""
    _query_and_import(_BASE_URL + _POS_DOC_QUERY, request_data, doc_type)


def query_sales(request_data: dict) -> None:
    """查詢 POS 銷貨明細（SO）並寫入 IFACE。"""
    _query_and_import(_BASE_URL + _POS_SALES_DOC, request_data, "SO")


# ---------------------------------------------------------------------------
# DocUpdate：CM 轉採購單後回傳 POS
# ---------------------------------------------------------------------------

def doc_update(erp_orders: dict) -> str:
    """
    將 CM 採購單資料回傳 RETEX POS，產生 ST 進貨驗收單。
    erp_orders：由 iface-db named-query 取得的 {'DocData': [...]} 結構。
    """
    if not erp_orders or not erp_orders.get("DocData"):
        return "{}"

    request_data = {"RequestData": erp_orders}
    json_data    = _call_api(_BASE_URL + _ERP_DOC_UPDATE, request_data)
    return json.dumps(json_data)
