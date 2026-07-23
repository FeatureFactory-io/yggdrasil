"""Payment API FastAPI entrypoint — technology container."""

from fastapi import FastAPI

app = FastAPI(title="Payment API")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.post("/charges")
def create_charge(amount: int) -> dict[str, int | str]:
    """Create a payment charge."""
    return {"id": "chg_1", "amount": amount}
