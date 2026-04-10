"""
對美金匯率 job（currencyapi.com）
對應 currencyAPI.py
"""

import os
import sys
import json
import requests
from iface_client import iface_import, run_procedure

_URL     = "https://api.currencyapi.com/v3/latest"
_API_KEY = os.environ["CURRENCY_API_KEY"]


def run() -> None:
    headers = {"apikey": _API_KEY}

    try:
        response = requests.get(_URL, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"HTTP 請求失敗: {e}")
        sys.exit(1)

    fetch_data = response.json()

    iface_import(_URL, fetch_data, {}, "currencyAPI", "RATE", {})

    # 匯入 IFACE..XX_TO_USD_RATE
    run_procedure("XXIF_CURRENCY_Rate_Import")
