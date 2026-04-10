#!/bin/bash
VALID_JOBS=("currency_api" "customs_rate")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$1" ]; then
    echo "Error: 請指定 job 名稱"
    echo "用法: $0 [$(IFS='|'; echo "${VALID_JOBS[*]}")]"
    exit 1
fi

JOB_NAME="$1"
VALID=0
for j in "${VALID_JOBS[@]}"; do
    [ "$j" = "$JOB_NAME" ] && VALID=1 && break
done

if [ "$VALID" -eq 0 ]; then
    echo "Error: 不支援的 job: $JOB_NAME"
    echo "有效 job: ${VALID_JOBS[*]}"
    exit 1
fi

cd "$SCRIPT_DIR"
docker compose run --rm iface-currency-fetcher python ./app/main.py "$JOB_NAME"
