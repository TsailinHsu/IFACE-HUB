"""
EIP LL 訂單 job（公司 B）
對應 eip/LLEIPOrder.py
MODULE=LLEIP，SP 名稱使用 LL 系列
"""

import eip_client
from iface_client import run_procedure, status_update

_IMPORT_STATUS   = 0
_SHIPPING_STATUS = "shipped"

_ORDER_TYPES  = [
    "line_gift", "shopee", "super_landing", "distributor",
    "shopify", "return_change", "repost", "requisit",
]
_RETURN_TYPES = ["return", "change", "refund"]


def run() -> None:
    # --- Fetch（eip_client 讀取 EIP_MODULE=LLEIP）---
    for source_type in _ORDER_TYPES:
        eip_client.order(_IMPORT_STATUS, _SHIPPING_STATUS, source_type)

    for return_type in _RETURN_TYPES:
        eip_client.order_return(_IMPORT_STATUS, return_type)

    eip_client.order_reject(_IMPORT_STATUS)
    eip_client.order_problem(_IMPORT_STATUS)
    eip_client.inventory_transfer(_IMPORT_STATUS)
    eip_client.inventory_change(_IMPORT_STATUS)

    # --- Import into Cosmos ERP（LL instance）---
    run_procedure("XXIF_COPTG_LL_Import")
    run_procedure("XXIF_COPTI_LL_Import")
    run_procedure("XXIF_INVTA_LL_Import")

    # --- Reply（LL reply views）---
    eip_client.order_reply()
    eip_client.order_return_reply()
    eip_client.order_reject_reply()
    eip_client.order_problem_reply()
    eip_client.order_requisit_reply()
    eip_client.inventory_transfer_reply()
    eip_client.inventory_change_reply()

    # --- Status Update（MODULE=LLEIP）---
    for source_type in _ORDER_TYPES:
        status_update("LLEIP", source_type, "5", "6")

    for return_type in _RETURN_TYPES:
        status_update("LLEIP", return_type, "5", "6")

    status_update("LLEIP", "orderReject",     "5", "6")
    status_update("LLEIP", "orderProblem",    "5", "6")
    status_update("LLEIP", "transfers",       "5", "6")
    status_update("LLEIP", "inventoryChange", "5", "6")
