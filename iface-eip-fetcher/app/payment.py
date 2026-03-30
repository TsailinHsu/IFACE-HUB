"""
EIP 請款單 job
對應 eip/EIPPayment.py
"""

import eip_client
from iface_client import run_procedure, status_update

_IMPORT_STATUS = 0


def run() -> None:
    # --- Fetch ---
    eip_client.payment_request(_IMPORT_STATUS)

    # --- Import into Cosmos ERP ---
    run_procedure("XXIF_ACPTA_Import")

    # --- Reply ---
    eip_client.payment_request_reply()

    # --- Status Update ---
    status_update("EIP", "請款單", "5", "6")
