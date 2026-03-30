"""
EIP Fetcher 通用執行引擎

讀取 YAML 設定檔，依序執行 fetch → procedures → reply → status_update。
不含任何業務知識，所有流程由 config/ 下的 YAML 驅動。
"""

import os
import pathlib
import yaml

import eip_client
from iface_client import run_procedure, status_update

_DEFAULT_CONFIG = pathlib.Path(__file__).parent.parent / "config" / "eip.yml"


def load_config() -> dict:
    config_file = os.getenv("EIP_CONFIG", str(_DEFAULT_CONFIG))
    with open(config_file, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _run_fetch(step: dict) -> None:
    t = step["type"]
    if t == "order":
        for source_type in step["source_types"]:
            eip_client.order(0, step["shipping_status"], source_type)
    elif t == "order_return":
        for return_type in step["return_types"]:
            eip_client.order_return(0, return_type)
    elif t == "order_reject":
        eip_client.order_reject(0)
    elif t == "order_problem":
        eip_client.order_problem(0)
    elif t == "inventory_transfer":
        eip_client.inventory_transfer(0)
    elif t == "inventory_change":
        eip_client.inventory_change(0)
    elif t == "payment_request":
        eip_client.payment_request(0)
    elif t == "pre_products":
        eip_client.pre_products(0)
    else:
        raise ValueError(f"Unknown fetch type: '{t}'")


def run_job(job_name: str) -> None:
    cfg = load_config()
    module = cfg["module"]
    job = cfg["jobs"].get(job_name)
    if job is None:
        valid = list(cfg["jobs"].keys())
        raise ValueError(f"Job '{job_name}' not found. Valid jobs: {valid}")

    print(f"[{module}:{job_name}] Step 1/4 — Fetch")
    for step in job.get("fetch", []):
        _run_fetch(step)

    print(f"[{module}:{job_name}] Step 2/4 — Run procedures")
    for proc in job.get("procedures", []):
        run_procedure(proc)

    print(f"[{module}:{job_name}] Step 3/4 — Reply")
    for r in job.get("reply", []):
        eip_client.reply(r["endpoint"], r["view"])

    print(f"[{module}:{job_name}] Step 4/4 — Status update")
    for func in job.get("status_functions", []):
        status_update(module, func, "5", "6")
