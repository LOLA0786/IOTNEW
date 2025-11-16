from fastapi import APIRouter
from pydantic import BaseModel
import yfinance as yf
import numpy as np

router = APIRouter()

class RiskRequest(BaseModel):
    symbol: str = "AAPL"
    days: int = 14

@router.post("/risk-check")
def risk_check(req: RiskRequest):
    symbol = req.symbol
    days = req.days
    hist = yf.Ticker(symbol).history(period=f"{max(days,14)}d", interval="1d")
    if hist.empty or len(hist) < 5:
        return {"symbol": symbol, "error": "not_enough_data"}

    # daily returns
    close = hist["Close"].values
    returns = np.diff(close) / close[:-1]
    vol = float(np.std(returns) * np.sqrt(252) * 100)  # annualized volatility in %
    # ATR (average true range) approx
    high = hist["High"].values
    low = hist["Low"].values
    tr = np.maximum(high[1:] - low[1:], np.maximum(abs(high[1:] - close[:-1]), abs(low[1:] - close[:-1])))
    atr = float(np.mean(tr[-days:])) if len(tr) >= days else float(np.mean(tr))

    # simple recommendation: if vol > 60% (very high) -> avoid, else ok
    recommendation = "ok"
    if vol > 60:
        recommendation = "avoid_high_volatility"
    elif vol > 30:
        recommendation = "high_volatility_caution"
    elif vol < 15:
        recommendation = "low_volatility_ok"

    return {
        "symbol": symbol,
        "volatility_annual_percent": round(vol,2),
        "atr": round(atr,4),
        "recommendation": recommendation
    }
