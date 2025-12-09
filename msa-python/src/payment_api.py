from datetime import datetime
import uuid

from fastapi import FastAPI
from pydantic import BaseModel

from .kafka_producer import create_producer, send_event

app = FastAPI(title = "payment-api")

producer = create_producer()

class PaymentApprovalRequest(BaseModel):
    order_id: str
    user_id: str
    amount: int
    method: str


@app.post("/payments/approve")
async def approve_payment(req: PaymentApprovalRequest):
    payment_id = str(uuid.uuid4())
    
    payment_event = {
        "event_type": "payment.approved",
        "payment_id": payment_id,
        "order_id": req.order_id,
        "user_id": req.user_id,
        "amount": req.amount,
        "method": req.method,
        "approved_at": datetime.utcnow().isoformat(),
        "source": "payment-api",
        "version": "v1",
    }
    
    send_event(
        producer = producer,
        topic = "payments",
        key = req.order_id,
        value = payment_event,
    )
    
    log_event = {
        "event_type": "log.payment.approved",
        "order_id": req.order_id,
        "payment_id": payment_id,
        "user_id": req.user_id,
        "amount": req.amount,
        "created_at": datetime.utcnow().isoformat(),
        "source": "payment-api",
        "version": "v1",
    }
    
    send_event(
        producer = producer,
        topic = "logs",
        key = req.order_id,
        value = log_event,
    )
    
    return {
        "status": "approved",
        "payment_id": payment_id,
        "event": payment_event
    }
