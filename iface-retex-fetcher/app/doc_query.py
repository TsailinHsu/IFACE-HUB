"""
RETEX 單據查詢補跑 job — 指定單據類型與日期區間，寫入 IFACE，不執行匯入 SP

用法：python app/main.py doc_query <DocTyNo> <start_date> <end_date>
      DocTyNo：ST | BO | MO | ME
      日期格式：YYYY/MM/DD
範例：python app/main.py doc_query ST 2026/04/01 2026/04/14

目的：補跑指定單據類型的查詢並寫入 IFACE，由人工決定是否後續執行匯入 SP。
      不使用 DataStamp，以 StDate/EdDate 為唯一過濾條件。
"""

import retex_client

_ALLOWED_DOC_TYPES = {"ST", "BO", "MO", "ME"}


def run(doc_ty_no: str, start_date: str, end_date: str) -> None:
    if doc_ty_no not in _ALLOWED_DOC_TYPES:
        raise SystemExit(f"DocTyNo 必須為 {' | '.join(sorted(_ALLOWED_DOC_TYPES))}，收到：{doc_ty_no!r}")

    print(f"RETEX doc_query: DocTyNo={doc_ty_no}  {start_date} ~ {end_date}")

    request_data = {
        "RequestData": {
            "DocTyNo": doc_ty_no,
            "StDate":  start_date,
            "EdDate":  end_date,
        }
    }
    retex_client.query_docs(request_data, doc_ty_no)
    print(f"doc_query ({doc_ty_no}) 已寫入 IFACE，請手動確認後執行對應匯入 SP。")
