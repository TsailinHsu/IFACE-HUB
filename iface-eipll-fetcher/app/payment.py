"""EIP LL 請款單 job（公司 B）"""

import eip_client
from iface_client import run_procedure, status_update

_IMPORT_STATUS = 0


def run() -> None:
    eip_client.payment_request(_IMPORT_STATUS)
    run_procedure("XXIF_ACPTA_LL_Import")
    eip_client.payment_request_reply()
    status_update("LLEIP", "請款單", "5", "6")
