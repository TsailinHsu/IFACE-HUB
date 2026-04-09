"""
xdelivery 退貨 job（前 1 日）
對應 xdelivery/xdelivery.py

注意：銷貨單（order_sale）需人工重分類，不自動匯入，此 job 不處理。
      自 2024/04/03 起 ERP 匯入改由 EIP API 處理，此 job 僅收集資料。
"""

from datetime import datetime, timedelta
import xdelivery_client

_STOCK_IN = 1  # 是否已扣庫存：1=是


def run() -> None:
    begin_date = datetime.strftime(datetime.now() - timedelta(1), "%Y/%m/%d")
    end_date   = begin_date
    print(f"xdelivery order: {begin_date}")

    # 銷貨單
    xdelivery_client.solds("order_sale",      begin_date, end_date, "COPTG", "銷貨單")

    # 銷退單（整筆退）
    xdelivery_client.solds("order_return",    begin_date, end_date, "COPTI", "銷退單")

    # 退換貨（部分退）
    xdelivery_client.solds("order_item_back", begin_date, end_date, "COPTI", "退換貨")

    # 收件人退貨（經銷退貨，人工處理，僅收集）
    xdelivery_client.recipient_returneds(_STOCK_IN, begin_date, end_date, "COPTI", "經銷退貨")
