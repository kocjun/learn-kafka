import json
import time
from typing import Any, Dict, List

from confluent_kafka import Producer
import psycopg

from ..common.config import settings
from ..kafka_producer import create_producer


STATUS_PENDING = "pending"
STATUS_PUBLISHING = "publishing"
STATUS_PUBLISHED = "published"
STATUS_FAILED = "failed"


def fetch_outbox_batch(cur: psycopg.Cursor, batch_size: int) -> List[Dict[str, Any]]:
    cur.execute(
        """
        SELECT id, aggregate_type, aggregate_id, event_type, event_id, payload, retry_count
        FROM outbox
        WHERE status = %s
        ORDER BY created_at
        FOR UPDATE SKIP LOCKED
        LIMIT %s
        """,
        (STATUS_PENDING, batch_size),
    )
    rows = cur.fetchall()
    # 점유 상태 업데이트
    if rows:
        ids = [row["id"] for row in rows]
        cur.execute(
            """
            UPDATE outbox
            SET status = %s, last_attempt_at = NOW()
            WHERE id = ANY(%s)
            """,
            (STATUS_PUBLISHING, ids),
        )
    return rows


def mark_published(cur: psycopg.Cursor, outbox_id: int) -> None:
    cur.execute(
        """
        UPDATE outbox
        SET status = %s, published_at = NOW(), error = NULL
        WHERE id = %s
        """,
        (STATUS_PUBLISHED, outbox_id),
    )


def mark_failed(cur: psycopg.Cursor, outbox_id: int, retry_count: int, error: str) -> None:
    next_status = STATUS_FAILED if retry_count + 1 >= settings.outbox_retry_limit else STATUS_PENDING
    cur.execute(
        """
        UPDATE outbox
        SET status = %s, retry_count = retry_count + 1, error = %s, last_attempt_at = NOW()
        WHERE id = %s
        """,
        (next_status, error, outbox_id),
    )


def publish_record(producer: Producer, record: Dict[str, Any]) -> None:
    envelope = {
        "meta": {
            "event_type": record["event_type"],
            "event_version": "v1",
            "event_id": str(record["event_id"]),
            "source": "outbox-publisher",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "data": record["payload"],
    }
    producer.produce(
        topic=record["aggregate_type"],
        key=str(record["aggregate_id"]).encode("utf-8"),
        value=json.dumps(envelope).encode("utf-8"),
    )
    producer.poll(0)


def run_once() -> None:
    producer = create_producer(settings.kafka_bootstrap_servers)
    with psycopg.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        autocommit=False,
    ) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            records = fetch_outbox_batch(cur, settings.outbox_batch_size)
            if not records:
                return
            for record in records:
                try:
                    publish_record(producer, record)
                    mark_published(cur, record["id"])
                except Exception as exc:  # noqa: BLE001
                    print(f"publish failed for outbox {record['id']}: {exc}")
                    mark_failed(cur, record["id"], record["retry_count"], str(exc))
            conn.commit()
    producer.flush()


def main() -> None:
    print("Outbox publisher started")
    while True:
        run_once()
        time.sleep(settings.outbox_poll_interval_seconds)


if __name__ == "__main__":
    main()
