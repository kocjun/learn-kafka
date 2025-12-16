import asyncio
from contextlib import contextmanager

import src.main as main
from src.main import OrderRequest


class DummyCursor:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None):
        # 간단히 호출 기록만 남김
        self.calls.append((query.strip(), params))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


@contextmanager
def dummy_transaction(cursor: DummyCursor):
    yield cursor


def test_create_order_enqueues_outbox(monkeypatch):
    cursor = DummyCursor()
    monkeypatch.setattr(main, "transaction", lambda: dummy_transaction(cursor))

    req = OrderRequest(
        order_id="order-1",
        user_id="user-1",
        product_id="prod-1",
        quantity=2,
    )
    result = asyncio.run(main.create_order(req))

    assert result["outbox_enqueued"] is True
    assert len(cursor.calls) == 2

    # 첫 번째 INSERT: orders
    _, order_params = cursor.calls[0]
    assert order_params[0] == "order-1"
    assert order_params[1] == "user-1"
    assert order_params[2] == "prod-1"
    assert order_params[3] == 2

    # 두 번째 INSERT: outbox
    _, outbox_params = cursor.calls[1]
    assert outbox_params[0] == "orders"
    assert outbox_params[1] == "order-1"
    assert outbox_params[2] == "order.created"
