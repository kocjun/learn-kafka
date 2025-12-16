import uuid
from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

from .common.config import settings
from .common.db import transaction
from .kafka_producer import wrap_event

app = FastAPI()

class OrderRequest(BaseModel):
    order_id: str | None = None
    user_id: str
    product_id: str
    quantity: int
    
@app.get("/")
def health():
    return {"status": "ok"}
    
@app.post("/orders")
async def create_order(req: OrderRequest):
    order_id = req.order_id or str(uuid.uuid4())

    event_data = {
        "order_id": order_id,
        "user_id": req.user_id,
        "product_id": req.product_id,
        "quantity": req.quantity,
        "created_at": datetime.utcnow().isoformat(),
        "version": "v1",
    }
    event = wrap_event(
        event_type="order.created",
        source="order-api",
        data=event_data,
    )

    # DB 트랜잭션으로 주문 + 아웃박스 기록
    with transaction() as cur:
        cur.execute(
            """
            INSERT INTO orders (id, user_id, product_id, quantity, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                order_id,
                req.user_id,
                req.product_id,
                req.quantity,
                "created",
                datetime.utcnow(),
            ),
        )
        cur.execute(
            """
            INSERT INTO outbox (
                aggregate_type,
                aggregate_id,
                event_type,
                event_id,
                payload,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                "orders",
                order_id,
                "order.created",
                uuid.uuid4(),
                event["data"],
                "pending",
            ),
        )

    return {
        "status": "success",
        "order_id": order_id,
        "outbox_enqueued": True,
        "kafka_topic": "orders",
        "outbox_table": settings.db_name,
    }
