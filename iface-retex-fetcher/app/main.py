"""
iface-retex-fetcher 入口
用法：python app/main.py <job>

job:
  daily   每日主排程（前一日所有單據 + ErpDocUpdate + DataStamp）
"""

import sys
import daily
import cm_ax_import
import so_import
import so_query

JOBS = {
    "daily":     daily.run,
    "cm_ax_import": cm_ax_import.run,
    "so_query":  so_query.run,
    "so_import": so_import.run,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in JOBS:
        print(f"用法: python app/main.py [{' | '.join(JOBS)}] [args...]")
        print("  cm_ax_import 需指定日期區間：cm_ax_import <start_date> <end_date>  (格式: YYYY/MM/DD)")
        print("  so_query  需指定日期區間：so_query  <start_date> <end_date>  (格式: YYYY/MM/DD)  # 診斷用，不寫入 IFACE")
        print("  so_import 需指定日期區間：so_import <start_date> <end_date>  (格式: YYYY/MM/DD)")
        sys.exit(1)

    job_name  = sys.argv[1]
    extra_args = sys.argv[2:]
    print(f"--- RETEX fetcher: {job_name} ---")
    JOBS[job_name](*extra_args)
    print(f"--- RETEX fetcher: {job_name} 完成 ---")


if __name__ == "__main__":
    main()
