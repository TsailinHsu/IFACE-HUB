"""
RETEX CM 門市補貨訂單 — 統一處理 job（不在 daily 自動排程中執行）

CM 訂單需人工於 XLS 匯出後確認，再手動執行本 job 統一處理，
分兩種倉別：
  - A000/A118/A119：通知倉庫出貨的通知單，不走採購單流程，
    只寫入 XX_POS_CM_HIST 歷史記錄（XXIF_RETEX_CM_A000_Import）。
  - 其他（含 M100009，關係人）：走一般採購單流程
    （XXIF_RETEX_CM_Import），寫入 PURTC/PURTD 並回傳 ERP 單號
    （CMxxx）給 RETEX POS。M100009 額外匯出 XLS 供人工確認。
未來視 WMS 系統建置，XLS 輸出將改為 WMS API 呼叫。

執行流程：
  1. 向 RETEX API 查詢指定日期區間的 CM 單據並寫入 IFACE
  2. 執行 XXIF_RETEX_CM_AX_QUERY SP，依每個 (DenNo, ShopNo) 組合
     匯出一份 .xls 檔案至 OUTPUT_DIR（預設 /output）
  3. 執行 XXIF_RETEX_CM_A000_Import，寫入 A000/A118/A119 歷史記錄
  4. 執行 RETEX_CM_A000_GET_ORDERS 取得 ERP 採購單，回傳 RETEX POS（ErpDocUpdate）
  5. 執行 XXIF_RETEX_CM_Import，其餘供應商轉一般採購單
  6. 執行 RETEX_CM_GET_ORDERS 取得 ERP 採購單，回傳 RETEX POS（ErpDocUpdate）

用法：python app/main.py cm_import <start_date> <end_date>
      日期格式：YYYY/MM/DD
"""

import os
from datetime import datetime, date

import xlwt

import retex_client
from iface_client import run_procedure, sp_query, named_query

_OUTPUT_DIR = os.getenv("CM_QUERY_OUTPUT_DIR", "/output")

_TASK_LIST = [
    ("A118", None),
    ("A119", None),
    ("M100009", None),
    ("A000", "BAA10"),
    ("A000", "BAA20"),
    ("A000", "BAA30"),
    ("A000", "BAA40"),
    ("A000", "BAA50"),
    ("A000", "BAA60"),
    ("A000", "BAB40"),
    ("A000", "BAB50"),
    ("A000", "BAC10"),
    ("A000", "BAC20"),
    ("A000", "BAC30"),
    ("A000", "BAC40"),
    ("A000", "BAC50"),
    ("A000", "BAA31"),
    ("A000", "BAA51"),
    ("A000", "BAA71"),
    ("A000", "BDA20"),
    ("A000", "BAC11"),
    ("A000", "BAA91"),
    ("A000", "BDC10"),
    ("A000", "BAC80"),
    ("A000", "BDA10"),
    ("A000", "BAA150"),
    ("A000", "BAB60"),
    ("A000", "BAA160"),
    ("A000", "BAC100")
]

_TEXT_STYLE = xlwt.easyxf(num_format_str="@")
_DATE_STYLE = xlwt.easyxf(num_format_str="YYYY/MM/DD")


def run(start_date: str, end_date: str) -> None:
    print(f"RETEX cm_import: {start_date} ~ {end_date}")

    # --- 1. 自 RETEX 取得指定日期區間的 CM 單據 ---
    retex_client.query_docs(
        {"RequestData": {"DocTyNo": "CM", "StDate": start_date, "EdDate": end_date}},
        "CM",
    )

    # --- 2. 匯出 XLS ---
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    today_str = datetime.today().strftime("%Y%m%d")

    for den_no, shop_no in _TASK_LIST:
        filename = f"{today_str}_{den_no}.xls" if shop_no is None else f"{today_str}_{den_no}_{shop_no}.xls"
        output_path = os.path.join(_OUTPUT_DIR, filename)

        try:
            rows = sp_query(
                "XXIF_RETEX_CM_AX_QUERY",
                params={"ShopNo": shop_no, "DenNo": den_no},
            )

            if not rows:
                print(f"⚠️  無資料，略過：{filename}")
                continue

            columns = list(rows[0].keys())
            barcode_col = next((i for i, c in enumerate(columns) if c.strip() == "商品條碼"), None)
            date_col    = next((i for i, c in enumerate(columns) if c.strip() == "建立日期"), None)

            wb = xlwt.Workbook()
            ws = wb.add_sheet("工作表1")

            for col_idx, col_name in enumerate(columns):
                ws.write(0, col_idx, col_name)

            for row_idx, row in enumerate(rows, start=1):
                for col_idx, col_name in enumerate(columns):
                    value = row.get(col_name)
                    if col_idx == barcode_col:
                        ws.write(row_idx, col_idx, str(value) if value is not None else "", _TEXT_STYLE)
                    elif col_idx == date_col:
                        if isinstance(value, str):
                            try:
                                value = datetime.strptime(value[:10], "%Y-%m-%d").date()
                            except ValueError:
                                value = None
                        ws.write(row_idx, col_idx, value if value is not None else "", _DATE_STYLE)
                    else:
                        ws.write(row_idx, col_idx, value)

            wb.save(output_path)
            print(f"✅  匯出：{output_path}")

        except Exception as e:
            print(f"❌  發生錯誤（{filename}）：{e}")
            continue

    run_procedure("XXIF_RETEX_CM_A000_Import")
    print("✅  CM A000/A118/A119 歷史記錄完成")

    # --- A000/A118/A119 轉採購單回傳 POS ---
    erp_orders = named_query("RETEX_CM_A000_GET_ORDERS")
    result = retex_client.doc_update(erp_orders)
    print("ErpDocUpdate (A000):", result)

    # --- 其餘供應商（含 M100009）轉一般採購單 ---
    run_procedure("XXIF_RETEX_CM_Import")
    print("✅  CM 一般採購單匯入完成")

    # --- 一般採購單回傳 POS（ErpDocNo 為 ERP 產生的 CMxxx 單號） ---
    create_date = datetime.today().strftime("%Y%m%d")
    erp_orders = named_query("RETEX_CM_GET_ORDERS", create_date=create_date)
    result = retex_client.doc_update(erp_orders)
    print("ErpDocUpdate (一般):", result)
