"""
iface-xdelivery-fetcher 入口
用法：python app/main.py <job>

job:
  order   退貨單（銷退 / 退換貨 / 收件人退貨）
  saas    Super Landing 服務費 / 簡訊儲值
"""

import sys
import order
import saas

JOBS = {
    "order": order.run,
    "saas":  saas.run,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in JOBS:
        print(f"用法: python app/main.py [{' | '.join(JOBS)}]")
        sys.exit(1)

    job_name = sys.argv[1]
    print(f"--- xdelivery fetcher: {job_name} ---")
    JOBS[job_name]()
    print(f"--- xdelivery fetcher: {job_name} 完成 ---")


if __name__ == "__main__":
    main()
