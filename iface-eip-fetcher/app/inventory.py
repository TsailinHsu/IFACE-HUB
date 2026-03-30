"""
EIP 庫存異動單 job（單獨執行用）
對應 eip/EIPInventoryChange.py

注意：order.py 的 run() 已包含庫存異動的完整流程（含 transfer）。
此 job 用於需要單獨補跑庫存異動的情境。
"""

import eip_client
from iface_client import run_procedure, status_update

_IMPORT_STATUS = 0


def run() -> None:
    # --- Fetch ---
    eip_client.inventory_change(_IMPORT_STATUS)
    eip_client.inventory_transfer(_IMPORT_STATUS)

    # --- Import into Cosmos ERP ---
    run_procedure("XXIF_INVTA_EIP_Import")

    # --- Reply ---
    eip_client.inventory_change_reply()
    eip_client.inventory_transfer_reply()

    # --- Status Update ---
    status_update("EIP", "inventoryChange", "5", "6")
    status_update("EIP", "transfers",       "5", "6")
