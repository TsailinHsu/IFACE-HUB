"""
iface-retex-fetcher 入口
用法：python app/main.py <job>

job:
  daily   每日主排程（前一日所有單據 + ErpDocUpdate + DataStamp）
"""

import sys
import daily

JOBS = {
    "daily": daily.run,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in JOBS:
        print(f"用法: python app/main.py [{' | '.join(JOBS)}]")
        sys.exit(1)

    job_name = sys.argv[1]
    print(f"--- RETEX fetcher: {job_name} ---")
    JOBS[job_name]()
    print(f"--- RETEX fetcher: {job_name} 完成 ---")


if __name__ == "__main__":
    main()
