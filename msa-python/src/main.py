from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import uuid

from .kafka_producer import create_producer, send_event, wrap_event

app = FastAPI()

producer = create_producer()

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
    # order_id 가 없으면 생성
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
    
    # kafka "orders" 토픽으로 발행 
    send_event(
        producer = producer,
        topic = "orders",
        key = order_id, 
        value = event,
    )
    
    # client 응답
    return {
        "status": "success",
        "order_id": order_id,
        "event": event,
    }
