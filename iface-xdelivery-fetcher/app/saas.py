"""
xdelivery SaaS 服務費 / 簡訊儲值 job
對應 xdelivery/xdeliverySaaS.py
"""

import xdelivery_client

_STATUS        = "pending"
_INVOICE_STATUS = "1"


def run() -> None:
    # 抓取服務費與儲值資料
    xdelivery_client.saas(_STATUS, _INVOICE_STATUS)

    # 匯入 Cosmos ERP（由 iface-db 呼叫 SP）
    from iface_client import run_procedure
    run_procedure("XXIF_COPTG_SaaS_Import")

    # 回傳單號至 Super Landing
    xdelivery_client.saas_reply()
