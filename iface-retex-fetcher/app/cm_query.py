"""
RETEX CM AX Query — 輸出門市訂單採購單為 XLS

執行 XXIF_RETEX_CM_AX_QUERY SP，依每個 (DenNo, ShopNo) 組合
匯出一份 .xls 檔案至 OUTPUT_DIR（預設 /output）。
"""

import os
from datetime import datetime, date

import xlwt

from iface_client import sp_query

_OUTPUT_DIR = os.getenv("CM_QUERY_OUTPUT_DIR", "/output")

_TASK_LIST = [
    ("A118", None),
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
]

_TEXT_STYLE = xlwt.easyxf(num_format_str="@")
_DATE_STYLE = xlwt.easyxf(num_format_str="YYYY/MM/DD")


def run() -> None:
    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    today_str = datetime.today().strftime("%Y%m%d")

    for den_no, shop_no in _TASK_LIST:
        filename = f"{today_str}_{den_no}.xls" if den_no == "A118" else f"{today_str}_{den_no}_{shop_no}.xls"
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
