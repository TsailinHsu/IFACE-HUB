"""
海關三旬匯率 job（portal.sw.nat.gov.tw）
對應 customsRate.py
"""

import sys
import requests
from iface_client import iface_import, run_procedure

_URL = "https://portal.sw.nat.gov.tw/APGQ/GC331!downLoad?formBean.downLoadFile=CURRENT_JSON"


def run() -> None:
    try:
        response = requests.get(_URL, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"HTTP 請求失敗: {e}")
        sys.exit(1)

    fetch_data = response.json()

    iface_import(_URL, fetch_data, {}, "CUSTOMS", "RATE", {})

    # 匯入 IFACE..XX_CUSTOMS_RATE
    run_procedure("XXIF_CUSTOMS_Rate_Import")
