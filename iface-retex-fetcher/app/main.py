"""
iface-retex-fetcher 入口
用法：python app/main.py <job>

job:
  daily   每日主排程（前一日所有單據 + ErpDocUpdate + DataStamp）
"""

import sys
import daily
import cm_query
import so_import

JOBS = {
    "daily":     daily.run,
    "cm_query":  cm_query.run,
    "so_import": so_import.run,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in JOBS:
        print(f"用法: python app/main.py [{' | '.join(JOBS)}] [args...]")
        print("  so_import 需指定日期區間：so_import <start_date> <end_date>  (格式: YYYY/MM/DD)")
        sys.exit(1)

    job_name  = sys.argv[1]
    extra_args = sys.argv[2:]
    print(f"--- RETEX fetcher: {job_name} ---")
    JOBS[job_name](*extra_args)
    print(f"--- RETEX fetcher: {job_name} 完成 ---")


if __name__ == "__main__":
    main()
