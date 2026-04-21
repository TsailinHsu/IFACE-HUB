"""
RETEX SO 銷貨查詢補跑 job — 指定日期區間，寫入 IFACE，不執行匯入 SP

用法：python app/main.py so_query <start_date> <end_date>
      日期格式：YYYY/MM/DD
範例：python app/main.py so_query 2025/01/01 2025/01/31

目的：補跑 SO 資料並寫入 IFACE，由人工確認後再手動執行 XXIF_RETEX_SO_Import。
      與 so_import 的差異：so_import 查詢後立即執行 SP；so_query 僅寫入 IFACE。
"""

import retex_client


def run(start_date: str, end_date: str) -> None:
    print(f"RETEX so_query: {start_date} ~ {end_date}")

    retex_client.query_sales({
        "RequestData": {"StDate": start_date, "EdDate": end_date}
    })

    print("so_query 已寫入 IFACE，請手動確認後執行 XXIF_RETEX_SO_Import。")
