from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time, uuid, json, os
from typing import List

router = APIRouter(prefix="/broker", tags=["Broker"])

POSITIONS_FILE = os.getenv("BROKER_POSITIONS", "./broker_positions.jsonl")

class Order(BaseModel):
    symbol: str
    side: str  # buy/sell
    qty: float
    price: float | None = None
    strategy: str | None = None

def append_line(path, obj):
    with open(path, "a") as f:
        f.write(json.dumps(obj) + "\\n")

def read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path,"r") as f:
        return [json.loads(l) for l in f if l.strip()]

@router.post("/order")
def place_order(o: Order):
    oid = str(uuid.uuid4())
    ts = int(time.time())
    # Simulated immediate fill at provided price or market price (provided)
    fill_price = o.price if o.price is not None else None
    record = {
        "id": oid,
        "symbol": o.symbol,
        "side": o.side,
        "qty": o.qty,
        "price": fill_price,
        "strategy": o.strategy,
        "status": "filled",
        "filled_at": ts
    }
    append_line(POSITIONS_FILE, record)
    return {"ok": True, "order": record}

@router.get("/positions")
def list_positions():
    return {"positions": read_lines(POSITIONS_FILE)}

@router.get("/history")
def history():
    return {"history": read_lines(POSITIONS_FILE)}
