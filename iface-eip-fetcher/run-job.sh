#!/bin/bash
#
# iface-eip-fetcher job runner
#
# 用法：
#   ./run-job.sh <job>              # 公司 A，使用 .env
#   ./run-job.sh -e .env.ll <job>  # 公司 B，使用 .env.ll
#
# 範例：
#   ./run-job.sh order
#   ./run-job.sh -e .env.ll payment
#

ENV_FILE=".env"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while getopts "e:" opt; do
    case "$opt" in
        e) ENV_FILE="$OPTARG" ;;
        *) ;;
    esac
done
shift $((OPTIND - 1))

if [ -z "$1" ]; then
    echo "Error: 請指定 job 名稱"
    echo "用法: $0 [-e env_file] <job>"
    exit 1
fi

cd "$SCRIPT_DIR"
docker compose --env-file "$ENV_FILE" run --rm iface-eip-fetcher python ./app/main.py "$1"
