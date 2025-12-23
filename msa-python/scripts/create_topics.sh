#!/usr/bin/env bash
set -euo pipefail
exec > >(tee -a /tmp/create_topics.log) 2>&1
set -x

BOOTSTRAP="${BOOTSTRAP:-kafka:9092}"

echo "Waiting for Kafka at ${BOOTSTRAP}..."
for i in $(seq 1 10); do
  if kafka-topics --bootstrap-server "${BOOTSTRAP}" --list >/dev/null 2>&1; then
    echo "Kafka is reachable"
    break
  fi
  echo "Kafka not ready, retrying (${i}/10)..."
  sleep 3
done

TOPICS=(
  orders
  payments
  inventory
  shipping
  logs
  metric.product.order_count
  metric.orders.per_minute
)

for topic in "${TOPICS[@]}"; do
  kafka-topics --bootstrap-server "${BOOTSTRAP}" \
    --create --if-not-exists \
    --topic "${topic}" \
    --replication-factor 1 \
    --partitions 3 || true
  kafka-topics --bootstrap-server "${BOOTSTRAP}" --describe --topic "${topic}" || true
done
