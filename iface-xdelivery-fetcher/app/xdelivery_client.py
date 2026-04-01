"""
xdelivery / Super Landing API 客戶端
"""

import json
import os
import requests
from iface_client import iface_import, get_reply

_ACCESS_KEY    = os.getenv("XDELIVERY_ACCESS_KEY", "")
_MERCHANT_ID   = int(os.getenv("XDELIVERY_MERCHANT_ID", "1"))
_MERCHANT_NAME = os.getenv("XDELIVERY_MERCHANT_NAME", "光速火箭有限公司")

_XDELIVERY_API = "https://system-api.xdelivery.io/merchants"

_SAAS_URLS = [
    "https://system-api-app.super-landing.com/billings.json",
    "https://system-api-www.super-landing.com/billings.json",
    "https://system-api-kafen.super-landing.com/billings.json",
    "https://system-api-app.super-landing.com/deposits.json",
    "https://system-api-www.super-landing.com/deposits.json",
    "https://system-api-kafen.super-landing.com/deposits.json",
]


def _fetch_all(api_url: str, query: dict, module: str, function: str) -> None:
    """分頁抓取所有資料並寫入 IFACE。"""
    all_data: list = []
    curr_page = 1

    while True:
        params = {**query, "page": curr_page}
        print(api_url, params)

        try:
            resp = requests.get(api_url, params=params, timeout=30)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        fetched    = json.loads(resp.text)
        page_count = fetched.get("total_pages", 1)
        count      = fetched.get("count", 0)
        print(f"count={count}  page={curr_page}/{page_count}")

        all_data.extend(fetched.get("data", []))
        curr_page += 1
        if curr_page > page_count:
            break

    merchants = {
        "merchants_id":    _MERCHANT_ID,
        "merchants_title": _MERCHANT_NAME,
    }
    if all_data:
        iface_import(api_url, {"data": all_data}, query, module, function, merchants)
    else:
        iface_import(api_url, {"data": []}, query, module, function, merchants, initial_status="6")


# ---------------------------------------------------------------------------
# Fetch functions
# ---------------------------------------------------------------------------

def solds(date_range_type: str, begin_date: str, end_date: str,
          module: str, function: str) -> None:
    """銷貨 / 退貨 / 退換貨"""
    _fetch_all(
        f"{_XDELIVERY_API}/solds.json",
        {
            "date_range_type": date_range_type,
            "begin_date":      begin_date,
            "end_date":        end_date,
            "access_key":      _ACCESS_KEY,
            "merchant_id":     _MERCHANT_ID,
        },
        module, function,
    )


def recipient_returneds(stock_in: int, begin_date: str, end_date: str,
                        module: str, function: str) -> None:
    """收件人退貨單（經銷退貨）"""
    _fetch_all(
        f"{_XDELIVERY_API}/recipient_returneds.json",
        {
            "begin_date":  begin_date,
            "end_date":    end_date,
            "access_key":  _ACCESS_KEY,
            "stock_in":    stock_in,
            "merchant_id": _MERCHANT_ID,
        },
        module, function,
    )


def saas(status_code: str, invoice_status: str) -> None:
    """Super Landing 服務費 / 簡訊儲值"""
    query = {
        "status":     status_code,
        "invoice":    invoice_status,
        "access_key": _ACCESS_KEY,
    }
    merchants = {
        "merchants_id":    _MERCHANT_ID,
        "merchants_title": _MERCHANT_NAME,
    }
    for url in _SAAS_URLS:
        all_data: list = []
        curr_page = 1
        while True:
            params = {**query, "page": curr_page}
            try:
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"SaaS fetch error ({url}): {e}")
                break

            fetched    = json.loads(resp.text)
            page_count = fetched.get("total_pages", 1)
            all_data.extend(fetched.get("data", []))
            curr_page += 1
            if curr_page > page_count:
                break

        if all_data:
            iface_import(url, {"data": all_data}, query, "COPTG", "SaaS", merchants)
        else:
            iface_import(url, {"data": []}, query, "COPTG", "SaaS", merchants, initial_status="6")


# ---------------------------------------------------------------------------
# Reply functions
# ---------------------------------------------------------------------------

def saas_reply() -> None:
    """回傳 SaaS 服務費 / 儲值單號至 Super Landing"""
    items = get_reply("COPTG_SaaS_APPLY_vw")
    if not items:
        return

    params = {"access_key": _ACCESS_KEY}
    for item in items:
        ret_url = f"{item['URL']}/{item['ID']}/ok.json"
        data    = {**params, "id": item["ID"], "cosmos_ref_id": item["RefId"]}
        try:
            resp = requests.post(ret_url, params=data, timeout=30)
            resp.raise_for_status()
            print(ret_url, resp.status_code)
        except requests.exceptions.RequestException as err:
            print(f"SaaS reply error: {err}")
            continue
