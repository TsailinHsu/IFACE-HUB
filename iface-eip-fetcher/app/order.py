"""
EIP 訂單 job
對應 eip/EIPOrder.py
"""

import eip_client
from iface_client import run_procedure, status_update

_IMPORT_STATUS   = 0
_SHIPPING_STATUS = "shipped"

# 銷貨 source_type 清單
_ORDER_TYPES = [
    "line_gift",      # Line 禮物
    "shopee",         # 蝦皮
    "super_landing",  # 一頁商店
    "distributor",    # 經銷
    "shopify",        # Shopify
    "return_change",  # 退貨補寄
    "repost",         # 補寄單
    "requisit",       # 領料單
]

# 銷退 return_type 清單
_RETURN_TYPES = ["return", "change", "refund"]


def run() -> None:
    # --- Fetch ---
    for source_type in _ORDER_TYPES:
        eip_client.order(_IMPORT_STATUS, _SHIPPING_STATUS, source_type)

    for return_type in _RETURN_TYPES:
        eip_client.order_return(_IMPORT_STATUS, return_type)

    eip_client.order_reject(_IMPORT_STATUS)
    eip_client.order_problem(_IMPORT_STATUS)
    eip_client.inventory_transfer(_IMPORT_STATUS)
    eip_client.inventory_change(_IMPORT_STATUS)

    # --- Import into Cosmos ERP ---
    run_procedure("XXIF_COPTG_EIP_Import")   # 銷貨（含 return_change, repost, requisit）
    run_procedure("XXIF_COPTI_EIP_Import")   # 銷退（含 orderReject, orderProblem）
    run_procedure("XXIF_INVTA_EIP_Import")   # 庫存異動（含 transfers, inventoryChange）

    # --- Reply ---
    eip_client.order_reply()
    eip_client.order_return_reply()
    eip_client.order_reject_reply()
    eip_client.order_problem_reply()
    eip_client.order_requisit_reply()
    eip_client.inventory_transfer_reply()
    eip_client.inventory_change_reply()

    # --- Status Update ---
    for source_type in _ORDER_TYPES:
        status_update("EIP", source_type, "5", "6")

    for return_type in _RETURN_TYPES:
        status_update("EIP", return_type, "5", "6")

    status_update("EIP", "orderReject",      "5", "6")
    status_update("EIP", "orderProblem",     "5", "6")
    status_update("EIP", "transfers",        "5", "6")
    status_update("EIP", "inventoryChange",  "5", "6")
