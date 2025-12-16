from types import SimpleNamespace

import src.producers.outbox_publisher as op


class FakeProducer:
    def __init__(self):
        self.produced = []
        self.flushed = False

    def produce(self, topic, key, value, callback=None):
        self.produced.append({"topic": topic, "key": key, "value": value})

    def poll(self, _):
        return None

    def flush(self):
        self.flushed = True


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.status = {str(row["id"]): "pending" for row in rows}

    def execute(self, query, params=None):
        q = " ".join(query.split())
        if "UPDATE outbox SET status" in q and "last_attempt_at" in q:
            ids = params[1]
            for oid in ids:
                self.status[str(oid)] = params[0]
        elif "UPDATE outbox SET status" in q and "published_at" in q:
            outbox_id = params[1]
            self.status[str(outbox_id)] = params[0]
        elif "UPDATE outbox SET status" in q and "retry_count" in q:
            outbox_id = params[2]
            self.status[str(outbox_id)] = params[0]

    def fetchall(self):
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.committed = False

    def cursor(self, *_, **__):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_outbox_run_once_publishes_and_updates(monkeypatch):
    rows = [
        {
            "id": 1,
            "aggregate_type": "orders",
            "aggregate_id": "order-123",
            "event_type": "order.created",
            "event_id": "evt-1",
            "payload": {"order_id": "order-123"},
            "retry_count": 0,
        }
    ]
    cursor = FakeCursor(rows)
    conn = FakeConn(cursor)
    producer = FakeProducer()

    monkeypatch.setattr(op, "create_producer", lambda *_: producer)
    monkeypatch.setattr(op.psycopg, "connect", lambda **__: conn)
    monkeypatch.setattr(op.psycopg, "rows", SimpleNamespace(dict_row=None))

    op.run_once()

    assert len(producer.produced) == 1
    assert cursor.status["1"] == op.STATUS_PUBLISHED
    assert conn.committed is True
    assert producer.flushed is True
