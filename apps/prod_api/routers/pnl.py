from fastapi import APIRouter
from apps.prod_api.db_models import SessionLocal, PnL, Trade, Position
import yfinance as yf

router = APIRouter(prefix="/pnl", tags=["PnL"])

@router.get("/summary")
def pnl_summary():
    db = SessionLocal()
    try:
        total_profit = 0.0
        rows = db.query(PnL).all()
        for r in rows:
            total_profit += (r.profit or 0.0)
        open_positions = db.query(Position).filter(Position.qty>0).all()
        return {"total_profit": total_profit, "open_positions": [{"symbol":p.symbol,"qty":p.qty,"avg_price":p.avg_price} for p in open_positions]}
    finally:
        db.close()
