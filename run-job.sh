#!/bin/bash
#
# iface-hub job runner
#
# 用法：
#   ./run-job.sh -e <env_file> <fetcher> <job>
#
# fetcher:
#   eip        iface-eip-fetcher（order / payment / pre_products / inventory）
#   retex      iface-retex-fetcher（daily）
#   xdelivery  iface-xdelivery-fetcher（order / saas）
#
# 範例：
#   ./run-job.sh -e .env.a eip order
#   ./run-job.sh -e .env.a eip payment
#   ./run-job.sh -e .env.b eip order        # 公司 B
#   ./run-job.sh -e .env.a retex daily
#   ./run-job.sh -e .env.a xdelivery saas
#
# 初始化資料庫（首次部署）：
#   ./run-job.sh -e .env.a init
#

set -euo pipefail

ENV_FILE=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while getopts "e:" opt; do
    case "$opt" in
        e) ENV_FILE="$OPTARG" ;;
        *) ;;
    esac
done
shift $((OPTIND - 1))

if [ -z "$ENV_FILE" ] || [ ! -f "$SCRIPT_DIR/$ENV_FILE" ]; then
    echo "Error: 請以 -e 指定存在的 env 檔"
    echo "用法: $0 -e <env_file> <fetcher> <job>"
    echo "      $0 -e <env_file> init"
    exit 1
fi

FETCHER="${1:-}"
JOB="${2:-}"

if [ -z "$FETCHER" ]; then
    echo "Error: 請指定 fetcher 或 init"
    echo "用法: $0 -e $ENV_FILE <fetcher> <job>"
    echo "      $0 -e $ENV_FILE init"
    exit 1
fi

cd "$SCRIPT_DIR"

if [ "$FETCHER" = "init" ]; then
    docker compose --env-file "$ENV_FILE" --profile init run --build --rm iface-initdb
    docker compose --env-file "$ENV_FILE" --profile init down --rmi local
    exit 0
fi

if [ -z "$JOB" ]; then
    echo "Error: 請指定 job 名稱"
    echo "用法: $0 -e $ENV_FILE $FETCHER <job>"
    exit 1
fi

SERVICE="iface-${FETCHER}-fetcher"
PROFILE="$FETCHER"

docker compose --env-file "$ENV_FILE" up -d iface-db
docker compose --env-file "$ENV_FILE" --profile "$PROFILE" \
    run --rm "$SERVICE" python app/main.py "$JOB"
