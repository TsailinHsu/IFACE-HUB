"""
iface-eipll-fetcher 入口（公司 B）
用法：python app/main.py <job>

job:
  order         訂單（銷貨、銷退、庫存異動）
  payment       請款單
  pre_products  品號申請
"""

import sys
import order
import payment
import pre_products

JOBS = {
    "order":        order.run,
    "payment":      payment.run,
    "pre_products": pre_products.run,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in JOBS:
        print(f"用法: python app/main.py [{' | '.join(JOBS)}]")
        sys.exit(1)

    job_name = sys.argv[1]
    print(f"--- EIP LL fetcher: {job_name} ---")
    JOBS[job_name]()
    print(f"--- EIP LL fetcher: {job_name} 完成 ---")


if __name__ == "__main__":
    main()
