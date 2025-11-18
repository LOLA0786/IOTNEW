from fastapi import APIRouter
from pydantic import BaseModel
import yfinance as yf, numpy as np

router = APIRouter(prefix="/candles", tags=["Candles"])

class CandlesReq(BaseModel):
    symbol: str = "AAPL"
    days: int = 14

@router.post("/pattern")
def detect_pattern(req: CandlesReq):
    sym = req.symbol
    days = req.days
    df = yf.Ticker(sym).history(period=f"{max(days,14)}d", interval="1d")
    if df.empty:
        return {"error":"no_data"}
    last = df.iloc[-2:]
    # simple pattern detection: bullish engulfing
    prev = last.iloc[0]
    cur = last.iloc[1]
    engulfing = (cur['Open'] < cur['Close']) and (cur['Open'] < prev['Close']) and (cur['Close'] > prev['Open'])
    pattern = "bullish_engulfing" if engulfing else "none"
    return {"symbol": sym, "pattern": pattern, "engulfing": engulfing}
