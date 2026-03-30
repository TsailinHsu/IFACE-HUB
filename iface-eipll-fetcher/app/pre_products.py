"""EIP LL 品號申請 job（公司 B）"""

import eip_client
from iface_client import run_procedure, status_update

_IMPORT_STATUS = 0


def run() -> None:
    eip_client.pre_products(_IMPORT_STATUS)
    run_procedure("XXIF_INVMB_LL_Import")
    eip_client.pre_products_reply()
    status_update("LLEIP", "preProducts", "5", "6")
