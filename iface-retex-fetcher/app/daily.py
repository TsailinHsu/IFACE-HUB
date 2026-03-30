"""
RETEX 每日主排程 job
對應 retex/retex.py

執行流程：
  1. 取得最新 DataStamp
  2. 查詢前一日各單據類型（PO/ST/BO/MO/ME/CM）
  3. 查詢前一日銷貨（SO）
  4. 匯入 Cosmos ERP（各 SP）
  5. CM 轉採購單後回傳 POS（ErpDocUpdate）
  6. 更新 DataStamp 高水位
"""

from datetime import datetime, timedelta

import retex_client
from iface_client import run_procedure, query_view, named_query

_DOC_TYPES = ["PO", "ST", "BO", "MO", "ME", "CM"]


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
    run_procedure("XXIF_RETEX_CM_Import")  # 補貨訂單

    # --- CM 轉採購單回傳 POS ---
    create_date = datetime.strftime(datetime.now(), "%Y%m%d")

    erp_orders = named_query("RETEX_CM_GET_ORDERS", create_date=create_date)
    result = retex_client.doc_update(erp_orders)
    print("ErpDocUpdate (一般):", result)

    erp_orders_a000 = named_query("RETEX_CM_A000_GET_ORDERS")
    result_a000 = retex_client.doc_update(erp_orders_a000)
    print("ErpDocUpdate (A000):", result_a000)

    # --- 更新 DataStamp ---
    run_procedure("XX_UPDATE_DATASTAMP")

    new_stamp_rows = query_view("XX_DATASTAMP")
    new_stamp = new_stamp_rows[0]["DataStamp"] if new_stamp_rows else None
    print(f"New DataStamp: {new_stamp}")
