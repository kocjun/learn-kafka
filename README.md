# Event-Driven E-commerce MSA (Kafka + Python)

## Overview
- 주문/재고/결제/배송/로그를 이벤트로 분리한 MSA PoC
- Kafka 기반 비동기 통신
- Outbox 패턴으로 DB–이벤트 정합성 보장
- DLQ, Retry/Backoff, Manual Commit 적용
- 실시간 집계(파생 지표 이벤트) 구현

## Architecture
- order-api (FastAPI)
- payment-api (FastAPI)
- inventory-worker (Consumer)
- shipping-worker (Consumer)
- metrics-worker (Stream/집계)
- outbox-publisher (Publisher)
- Kafka / Zookeeper / Kafka-UI

## Event Flow
1. order.created → orders
2. inventory.reserved/failed → inventory
3. payment.approved → payments
4. shipping.created → shipping
5. log.* → logs
6. metric.* → metrics.*

## Reliability
- Manual commit (success-only)
- Retry + Exponential Backoff
- DLQ (inventory.dlq 등)
- Idempotency (event_id)

## Run
```bash
docker compose up -d

