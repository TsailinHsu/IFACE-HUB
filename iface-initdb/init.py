"""
iface-initdb — 資料庫初始化腳本

啟動時連線 MSSQL，依序執行 initdb/ 內的 SQL 檔案。
所有 SQL 均為冪等（IF NOT EXISTS），可安全重複執行。
完成後以 exit(0) 退出，供 Docker init container 使用。
"""
import os
import re
import sys
import time
import glob
import pymssql


def get_connection() -> pymssql.Connection:
    return pymssql.connect(
        server=os.environ["IFACE_SERVER"],
        user=os.environ["IFACE_USER"],
        password=os.environ["IFACE_PWD"],
        database=os.environ.get("IFACE_DB", "IFACE"),
    )


def wait_for_db(retries: int = 12, delay: int = 5) -> pymssql.Connection:
    """等待資料庫就緒，最多重試 retries 次。"""
    for attempt in range(1, retries + 1):
        try:
            conn = get_connection()
            print(f"[initdb] Connected to database.")
            return conn
        except Exception as exc:
            print(f"[initdb] [{attempt}/{retries}] Not ready: {exc}")
            if attempt < retries:
                time.sleep(delay)
    print("[initdb] ERROR: Could not connect to database. Aborting.")
    sys.exit(1)


def execute_sql_file(conn: pymssql.Connection, filepath: str) -> None:
    """讀取 SQL 檔案，以 GO 為批次分隔符依序執行。"""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # GO 是 SSMS 批次分隔符，pymssql 不識別，需手動拆分
    batches = re.split(r"^\s*GO\s*$", content, flags=re.MULTILINE | re.IGNORECASE)

    cursor = conn.cursor()
    for batch in batches:
        batch = batch.strip()
        sql_lines = [l for l in batch.splitlines() if not l.strip().startswith("--")]
        if any(l.strip() for l in sql_lines):
            cursor.execute(batch)
    conn.commit()
    cursor.close()


def main() -> None:
    conn = wait_for_db()

    sql_dir = os.path.join(os.path.dirname(__file__), "initdb")
    sql_files = sorted(glob.glob(os.path.join(sql_dir, "*.sql")))

    if not sql_files:
        print("[initdb] WARNING: No SQL files found in initdb/")
        conn.close()
        return

    for filepath in sql_files:
        filename = os.path.basename(filepath)
        print(f"[initdb] Executing {filename} ...")
        try:
            execute_sql_file(conn, filepath)
            print(f"[initdb]   OK: {filename}")
        except Exception as exc:
            print(f"[initdb]   ERROR in {filename}: {exc}")
            conn.close()
            sys.exit(1)

    conn.close()
    print("[initdb] Initialization complete.")


if __name__ == "__main__":
    main()
