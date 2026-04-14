"""
RETEX SO 銷貨查詢 job — 指定日期區間，只顯示資料，不寫入 IFACE、不執行匯入 SP

用法：python app/main.py so_query <start_date> <end_date>
      日期格式：YYYY/MM/DD
範例：python app/main.py so_query 2025/01/01 2025/01/31

目的：補跑（so_import）前先診斷資料為何未於日常排程中匯入。
      依輸出結果判斷是否真的需要執行 so_import。
"""

from datetime import datetime

import retex_client

# SP 過濾條件：排除的門市代碼（與 usp_XXIF_RETEX_SO_Import.sql 一致）
_EXCLUDED_SHOPS = {"A000", "A001"}

# SP 過濾條件：BDate 最早有效日期
_MIN_BDATE = datetime(2026, 1, 1)


def run(start_date: str, end_date: str) -> None:
    print(f"RETEX so_query: {start_date} ~ {end_date}")
    print()

    data = retex_client.query_sales_raw({
        "RequestData": {"StDate": start_date, "EdDate": end_date}
    })

    result_no  = data.get("ResultNo",  "N/A")
    result_msg = data.get("ResultMsg", "")
    print(f"ResultNo : {result_no}")
    print(f"ResultMsg: {result_msg}")
    print()

    if result_no != "00":
        print("→ ResultNo != '00'：日常排程收到此回應會以 STATUS=6 略過，不寫入 IFACE。")
        print("  此日期區間不需補跑 so_import。")
        return

    records = data.get("SalesData", [])
    print(f"API 回傳筆數：{len(records)}")
    print()

    excluded     = []
    void_records = []
    valid        = []

    for rec in records:
        shop_no  = rec.get("ShopNo", "")
        hdd_vld  = rec.get("HHD_VLD", "")
        ecr_key  = rec.get("EcrHdKey", "?")
        amount   = rec.get("Amount", 0)
        b_date_raw = rec.get("BDate", "")

        try:
            b_date = datetime.fromisoformat(b_date_raw) if b_date_raw else None
        except ValueError:
            b_date = None

        row = {
            "EcrHdKey": ecr_key,
            "ShopNo":   shop_no,
            "BDate":    b_date_raw,
            "Amount":   amount,
            "HHD_VLD":  hdd_vld,
        }

        if shop_no in _EXCLUDED_SHOPS:
            excluded.append(row)
        elif hdd_vld == "D":
            void_records.append(row)
        elif b_date and b_date < _MIN_BDATE:
            row["_reason"] = f"BDate {b_date.date()} < {_MIN_BDATE.date()}（SP 硬過濾）"
            excluded.append(row)
        else:
            valid.append(row)

    # --- 有效（SP 不會過濾）---
    print(f"[有效，SP 會處理] {len(valid)} 筆")
    for r in valid:
        print(f"  {r['BDate'][:10]}  ShopNo={r['ShopNo']:<6}  Amount={r['Amount']:>10}  EcrHdKey={r['EcrHdKey']}")

    print()

    # --- 作廢 ---
    if void_records:
        print(f"[HHD_VLD='D' 作廢，SP 不處理] {len(void_records)} 筆")
        for r in void_records:
            print(f"  {r['BDate'][:10]}  ShopNo={r['ShopNo']:<6}  EcrHdKey={r['EcrHdKey']}")
        print()

    # --- 排除 ---
    if excluded:
        print(f"[SP 過濾排除] {len(excluded)} 筆")
        for r in excluded:
            reason = r.get("_reason") or f"ShopNo={r['ShopNo']} 在排除清單"
            print(f"  {r['BDate'][:10]}  ShopNo={r['ShopNo']:<6}  EcrHdKey={r['EcrHdKey']}  原因：{reason}")
        print()

    # --- 診斷結論 ---
    print("─" * 60)
    if not valid:
        print("結論：無有效記錄，不需補跑 so_import。")
    else:
        print(f"結論：有 {len(valid)} 筆有效記錄。")
        print("  若這些記錄未出現在 ERP，請依序確認：")
        print("  1. XX_POS_HIST — 已成功匯入 ERP 的 EcrHdKey 歷史紀錄")
        print("     SELECT * FROM XX_POS_HIST WHERE EcrHdKey IN (...)")
        print("     有記錄 → 已匯入，SP 正常排除，無需補跑")
        print()
        print("  2. IFACE STATUS — 查 IFACE WHERE APP_FUNCTION='SO' 及對應 EcrHdKey")
        print("     STATUS='E' → SP 執行時發生錯誤（查 ERROR_MESSAGE），修正後重跑 SP")
        print("     STATUS='0' → 資料已在 IFACE 待匯入，直接重跑 SP（勿重複呼叫 so_import）")
        print("     找不到記錄 → 日常排程未取得此筆，執行 so_import 補跑")
