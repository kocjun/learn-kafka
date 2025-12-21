#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -d "$ROOT_DIR/venv" ]]; then
  # 선택: 로컬 가상환경 활성화
  # shellcheck disable=SC1091
  source "$ROOT_DIR/venv/bin/activate"
fi

declare -a PIDS

start_proc() {
  local name="$1"; shift
  echo "[run_all] starting ${name}: $*"
  "$@" &
  local pid=$!
  PIDS+=($pid)
}

cleanup() {
  echo "[run_all] stopping all processes"
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done
}
trap cleanup INT TERM

# 필요한 프로세스들을 한 번에 실행
start_proc "order-api" uvicorn src.main:app --host 0.0.0.0 --port 8000
start_proc "outbox-publisher" python -m src.producers.outbox_publisher
start_proc "metrics-worker" python -m src.metrics_worker
# 필요 시 추가 워커/서비스를 아래에 활성화하세요
# start_proc "inventory-worker" python -m src.inventory_worker
# start_proc "shipping-worker" python -m src.shipping_worker
# start_proc "payment-api" uvicorn src.payment_api:app --host 0.0.0.0 --port 8001

status=0
# macOS 기본 bash 호환을 위해 wait -n 대신 수동 모니터링
while true; do
  all_exited=true
  for pid in "${PIDS[@]}"; do
    if kill -0 "$pid" 2>/dev/null; then
      all_exited=false
    else
      wait "$pid" 2>/dev/null || true
      status=$?
      echo "[run_all] process $pid exited with status $status, shutting down others"
      cleanup
      exit "$status"
    fi
  done
  if $all_exited; then
    break
  fi
  sleep 1
done
cleanup
exit "$status"
