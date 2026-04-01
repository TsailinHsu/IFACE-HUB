"""
EIP API 客戶端
封裝所有對 EIP API 的 HTTP 請求。
reply view 名稱與 endpoint 由呼叫端（pipeline）傳入，此處不硬編碼。
"""

import json
import os
import requests
from iface_client import iface_import, get_reply

_BASE_URL   = os.getenv("EIP_BASE_URL",   "https://api-eip.speeding-rocket.com")
_ACCESS_KEY = os.getenv("EIP_ACCESS_KEY", "")
_MODULE     = os.getenv("EIP_MODULE",     "EIP")   # 公司 A="EIP"，公司 B="LLEIP"


def _fetch_all(api_url: str, query: dict) -> dict:
    """
    分頁抓取所有資料，合併為單一 {'data': [...]} 結構。
    無資料時回傳 {'data': []}，不寫入 IFACE。
    """
    all_data: list = []
    curr_page = 1

    while True:
        params = {**query, "page": curr_page}
        print(api_url, params)

        try:
            resp = requests.get(api_url, params=params, timeout=30)
            resp.raise_for_status()
        except requests.exceptions.RequestException as err:
            print(f"HTTP Error: {err}")
            break

        fetched  = json.loads(resp.text)
        total    = fetched.get("total_entries", 0)
        pages    = fetched.get("total_pages",   1)
        print(f"total={total}  page={curr_page}/{pages}")

        all_data.extend(fetched.get("data", []))
        curr_page += 1
        if curr_page > pages:
            break

    return {"data": all_data}


def _api_call(endpoint: str, query: dict, function: str) -> None:
    """抓取資料並寫入 IFACE，無資料時以 STATUS='6' 標記已完成。"""
    api_url  = f"{_BASE_URL}{endpoint}"
    response = _fetch_all(api_url, query)

    if response["data"]:
        iface_import(api_url, response, query, _MODULE, function)
    else:
        iface_import(api_url, response, query, _MODULE, function, initial_status="6")


# ---------------------------------------------------------------------------
# Fetch functions
# ---------------------------------------------------------------------------

def order(import_status: int, shipping_status: str, source_type: str) -> None:
    """銷貨 / 退貨補寄 / 補寄單 / 領料單"""
    _api_call("/orders.json", {
        "source_type":     source_type,
        "imported":        import_status,
        "access_key":      _ACCESS_KEY,
        "shipping_status": shipping_status,
    }, source_type)


def order_return(import_status: int, return_type: str) -> None:
    """銷退單（return / change / refund）"""
    _api_call("/order_returns.json", {
        "imported":    import_status,
        "return_type": return_type,
        "access_key":  _ACCESS_KEY,
    }, return_type)


def order_reject(import_status: int) -> None:
    """拒收"""
    _api_call("/order_rejects.json", {
        "imported":   import_status,
        "access_key": _ACCESS_KEY,
    }, "orderReject")


def order_problem(import_status: int) -> None:
    """遺失"""
    _api_call("/order_problems.json", {
        "imported":   import_status,
        "access_key": _ACCESS_KEY,
    }, "orderProblem")


def inventory_transfer(import_status: int) -> None:
    """移倉單"""
    _api_call("/transfers.json", {
        "imported":   import_status,
        "access_key": _ACCESS_KEY,
    }, "transfers")


def inventory_change(import_status: int) -> None:
    """庫存異動單"""
    _api_call("/inventory_changes.json", {
        "imported":   import_status,
        "access_key": _ACCESS_KEY,
    }, "inventoryChange")


def payment_request(import_status: int) -> None:
    """請款單"""
    _api_call("/payment_requests.json", {
        "imported":   import_status,
        "access_key": _ACCESS_KEY,
    }, "請款單")


def pre_products(import_status: int) -> None:
    """品號申請"""
    _api_call("/pre_products.json", {
        "imported":   import_status,
        "access_key": _ACCESS_KEY,
    }, "preProducts")


def price_change(begin_date: str, end_date: str, field_type: str) -> None:
    """價格異動"""
    _api_call("/price_manage_request_items.json", {
        "begin_date": begin_date,
        "end_date":   end_date,
        "field_type": field_type,
        "access_key": _ACCESS_KEY,
    }, "priceChange")


# ---------------------------------------------------------------------------
# Reply：回寫 ERP 單號至 EIP
# endpoint 與 view_name 由 pipeline 從 YAML 傳入，此處不硬編碼
# ---------------------------------------------------------------------------

def reply(api_base: str, view_name: str) -> None:
    """
    從 IFACE reply view 取得 (ID, RefId) 清單，
    逐筆 POST 至 EIP /.../:id/ok.json
    """
    items = get_reply(view_name)
    if not items:
        return

    for item in items:
        url  = f"{_BASE_URL}{api_base}{item['ID']}/ok.json"
        data = {"access_key": _ACCESS_KEY, "id": item["ID"], "erp_ref_id": item["RefId"]}

        try:
            resp = requests.post(url, params=data, timeout=30)
            resp.raise_for_status()
            print(url, resp.status_code)
        except requests.exceptions.RequestException as err:
            print(f"Reply error: {err}")
            continue
