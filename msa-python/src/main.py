from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class OrderRequest(BaseModel):
    order_id: str
    user_id: str
    product_id: str
    quantity: int
    
@app.post("/orders")
async def create_order(req: OrderRequest):
    return {
        "status": "received",
        "order": req.dict()
    }