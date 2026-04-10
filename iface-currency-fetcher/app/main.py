"""
iface-currency-fetcher 入口
用法：python app/main.py <job>

job:
  currency_api   對美金匯率（currencyapi.com）
  customs_rate   海關三旬匯率（portal.sw.nat.gov.tw）
"""

import sys
import currency_api
import customs_rate

JOBS = {
    "currency_api": currency_api.run,
    "customs_rate":  customs_rate.run,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in JOBS:
        print(f"用法: python app/main.py [{' | '.join(JOBS)}]")
        sys.exit(1)

    job_name = sys.argv[1]
    print(f"--- currency fetcher: {job_name} ---")
    JOBS[job_name]()
    print(f"--- currency fetcher: {job_name} 完成 ---")


if __name__ == "__main__":
    main()
