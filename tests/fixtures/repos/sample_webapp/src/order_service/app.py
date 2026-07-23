"""Order Service — web container for order intake."""

from fastapi import FastAPI
from order_domain.service import OrderService

app = FastAPI(title="Order Service")
_order_service = OrderService()


@app.post("/orders")
def place_order(sku: str, qty: int = 1) -> dict[str, str]:
    """Accept an order and return its identifier."""
    order_id = _order_service.place_order(sku=sku, qty=qty)
    return {"order_id": order_id}
