"""Order domain service component."""


class OrderService:
    """Handles order placement and status queries."""

    def place_order(self, sku: str, qty: int) -> str:
        """Create an order and return its id."""
        return f"order-{sku}-{qty}"
