"""
RETEX SO 銷貨補跑 job — 指定日期區間

用法：python app/main.py so_import <start_date> <end_date>
      日期格式：YYYY/MM/DD
範例：python app/main.py so_import 2025/01/01 2025/01/31
"""

import retex_client
from iface_client import run_procedure


def run(start_date: str, end_date: str) -> None:
    print(f"RETEX so_import: {start_date} ~ {end_date}")

    retex_client.query_sales({
        "RequestData": {"StDate": start_date, "EdDate": end_date}
    })

    run_procedure("XXIF_RETEX_SO_Import")
