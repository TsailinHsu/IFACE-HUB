"""
iface-eip-fetcher 入口
用法：python app/main.py <job>

可用 job 由 EIP_CONFIG 指定的 YAML 設定檔決定：
  config/eip.yml   → 公司 A (EIP_MODULE=EIP)
  config/eipll.yml → 公司 B (EIP_MODULE=LLEIP)
"""

import sys
import pipeline


def main() -> None:
    cfg        = pipeline.load_config()
    module     = cfg["module"]
    valid_jobs = list(cfg["jobs"].keys())

    if len(sys.argv) < 2 or sys.argv[1] not in valid_jobs:
        print(f"用法: python app/main.py [{' | '.join(valid_jobs)}]")
        sys.exit(1)

    job_name = sys.argv[1]
    print(f"--- EIP fetcher [{module}]: {job_name} ---")
    pipeline.run_job(job_name)
    print(f"--- EIP fetcher [{module}]: {job_name} 完成 ---")


if __name__ == "__main__":
    main()
