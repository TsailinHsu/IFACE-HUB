"""
EIP 品號申請 job
對應 eip/EIPPreProducts.py
"""

import eip_client
from iface_client import run_procedure, status_update

_IMPORT_STATUS = 0


def run() -> None:
    # --- Fetch ---
    eip_client.pre_products(_IMPORT_STATUS)

    # --- Import into Cosmos ERP ---
    run_procedure("XXIF_INVMB_Import")

    # --- Reply ---
    eip_client.pre_products_reply()

    # --- Status Update ---
    status_update("EIP", "preProducts", "5", "6")
