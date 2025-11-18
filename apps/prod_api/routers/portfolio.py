from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from apps.prod_api.db_models import SessionLocal, Trade, Position, PnL, Portfolio
import datetime, json, yfinance as yf

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

class PlaceTradeReq(BaseModel):
    symbol: str
    side: str
    qty: float
    price: float | None = None
    strategy: str | None = None

@router.post("/place")
def place_trade(req: PlaceTradeReq):
    db = SessionLocal()
    try:
        price = req.price if req.price is not None else float(yf.Ticker(req.symbol).history(period="1d", interval="1m")["Close"].iloc[-1])
        # save trade record (simulated fill)
        t = Trade(
            symbol=req.symbol,
            price=price,
            sentiment="manual",
            reason=f"manual_{req.side}",
            score=0, boosted=0,
            decision="placed",
            saved=True,
            timestamp=datetime.datetime.utcnow(),
            strategy=req.strategy,
            raw={}
        )
        db.add(t); db.commit(); db.refresh(t)
        # update position
        pos = db.query(Position).filter(Position.symbol==req.symbol).first()
        if not pos:
            pos = Position(symbol=req.symbol, qty=0.0, avg_price=0.0)
        # simple avg price calc for buys; sells reduce qty
        if req.side.lower()=="buy":
            total_cost = (pos.avg_price * pos.qty) + (price * req.qty)
            pos.qty = pos.qty + req.qty
            pos.avg_price = total_cost / pos.qty if pos.qty>0 else 0
        else:
            pos.qty = pos.qty - req.qty
            if pos.qty < 0: pos.qty = 0
        pos.updated_at = datetime.datetime.utcnow()
        db.add(pos); db.commit()
        return {"ok": True, "trade": {"id": t.id, "symbol": t.symbol, "price": t.price}, "position": {"symbol": pos.symbol, "qty": pos.qty, "avg_price": pos.avg_price}}
    finally:
        db.close()

@router.get("/positions")
def list_positions():
    db = SessionLocal()
    try:
        ps = db.query(Position).all()
        return {"positions": [ {"symbol":p.symbol, "qty":p.qty, "avg_price":p.avg_price} for p in ps ]}
    finally:
        db.close()

@router.get("/trades")
def list_trades(limit:int=100):
    db = SessionLocal()
    try:
        ts = db.query(Trade).order_by(Trade.timestamp.desc()).limit(limit).all()
        return {"trades": [ {"symbol":t.symbol,"price":t.price,"decision":t.decision,"timestamp":t.timestamp.isoformat()} for t in ts ]}
    finally:
        db.close()

@router.post("/close")
def close_position(symbol: str, exit_price: float):
    db = SessionLocal()
    try:
        pos = db.query(Position).filter(Position.symbol==symbol).first()
        if not pos or pos.qty<=0:
            raise HTTPException(status_code=400, detail="no_position")
        # create PnL record closing entire position
        p = PnL(symbol=symbol, entry_price=pos.avg_price, exit_price=exit_price, qty=pos.qty, profit=(exit_price - pos.avg_price)*pos.qty, closed_at=datetime.datetime.utcnow(), status="closed", raw={})
        db.add(p)
        pos.qty = 0
        pos.avg_price = 0
        db.add(pos)
        db.commit()
        return {"ok":True, "pnl": {"symbol":p.symbol, "profit":p.profit}}
    finally:
        db.close()
