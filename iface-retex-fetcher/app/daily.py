"""
RETEX 每日主排程 job
對應 retex/retex.py

執行流程：
  1. 取得最新 DataStamp
  2. 查詢前一日各單據類型（PO/ST/BO/MO/ME）
  3. 查詢前一日銷貨（SO）
  4. 匯入 Cosmos ERP（各 SP）
  5. 更新 DataStamp 高水位

CM 門市補貨訂單不在此自動排程中處理，改由人工確認後
統一透過 cm_import job 處理（見 cm_import.py）。
"""

from datetime import datetime, timedelta

import retex_client
from iface_client import run_procedure, query_view

_DOC_TYPES = ["PO", "ST", "BO", "MO", "ME"]


def run() -> None:
    begin_date = datetime.strftime(datetime.now() - timedelta(1), "%Y/%m/%d")
    end_date   = begin_date
    print(f"RETEX daily: {begin_date}")

    # --- 取得最新 DataStamp ---
    data_stamp_rows = query_view("XX_DATASTAMP")
    data_stamp = data_stamp_rows[0]["DataStamp"] if data_stamp_rows else 0
    print(f"DataStamp: {data_stamp}")

    # --- 查詢各單據類型 ---
    for doc_type in _DOC_TYPES:
        request_data = {
            "RequestData": {
                "DocTyNo":   doc_type,
                "DataStamp": data_stamp,
                "StDate":    begin_date,
                "EdDate":    end_date,
            }
        }
        retex_client.query_docs(request_data, doc_type)

    # --- 查詢銷貨 SO ---
    retex_client.query_sales({
        "RequestData": {"StDate": begin_date, "EdDate": end_date}
    })

    # --- 匯入 Cosmos ERP ---
    run_procedure("XXIF_RETEX_BO_Import")  # 門市退貨
    run_procedure("XXIF_RETEX_ME_Import")  # 庫存調整
    run_procedure("XXIF_RETEX_MO_Import")  # 移倉出
    run_procedure("XXIF_RETEX_ST_Import")  # 進貨驗收
    run_procedure("XXIF_RETEX_SO_Import")  # 銷貨

    # --- 更新 DataStamp ---
    run_procedure("XX_UPDATE_DATASTAMP")

    new_stamp_rows = query_view("XX_DATASTAMP")
    new_stamp = new_stamp_rows[0]["DataStamp"] if new_stamp_rows else None
    print(f"New DataStamp: {new_stamp}")
