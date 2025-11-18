from fastapi import APIRouter
from pydantic import BaseModel
import yfinance as yf
import numpy as np
import pandas as pd

router = APIRouter(prefix="/risk", tags=["Risk"])

class RiskReq(BaseModel):
    symbol: str = "AAPL"
    days: int = 14

def compute_rsi(closes, period=14):
    deltas = np.diff(closes)
    seed = deltas[:period]
    up = seed[seed > 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = 100. - 100. / (1. + rs)
    rsi_vals = [rsi]
    up_ewm = down_ewm = None
    for delta in deltas[period:]:
        up_val = max(delta, 0)
        down_val = -min(delta, 0)
        up = (up * (period - 1) + up_val) / period
        down = (down * (period - 1) + down_val) / period
        rs = up / down if down != 0 else 0
        rsi_vals.append(100. - 100. / (1. + rs))
    return float(rsi_vals[-1])

@router.post("/check")
def risk_check(req: RiskReq):
    s = req.symbol
    days = req.days
    hist = yf.Ticker(s).history(period=f"{max(days,30)}d", interval="1d")
    if hist.empty or len(hist) < 10:
        return {"symbol": s, "error": "not_enough_data"}
    close = hist["Close"].values
    high = hist["High"].values
    low = hist["Low"].values

    # Volatility (annualized %)
    returns = np.diff(close) / close[:-1]
    vol = float(np.std(returns) * np.sqrt(252) * 100)

    # ATR (simple)
    tr = np.maximum(high[1:] - low[1:], np.maximum(abs(high[1:] - close[:-1]), abs(low[1:] - close[:-1])))
    atr = float(np.mean(tr[-days:])) if len(tr) >= days else float(np.mean(tr))

    # RSI
    try:
        rsi = compute_rsi(close, period=14)
    except Exception:
        rsi = None

    # MACD (12/26)
    ema12 = pd.Series(close).ewm(span=12, adjust=False).mean()
    ema26 = pd.Series(close).ewm(span=26, adjust=False).mean()
    macd = float((ema12 - ema26).iloc[-1])
    signal = float(pd.Series(ema12 - ema26).ewm(span=9, adjust=False).mean().iloc[-1])

    rec = "ok"
    if vol > 60:
        rec = "avoid_high_vol"
    elif vol > 30:
        rec = "caution_high_vol"
    elif rsi is not None and rsi > 80:
        rec = "overbought"
    elif rsi is not None and rsi < 20:
        rec = "oversold"

    return {
        "symbol": s,
        "volatility_annual_percent": round(vol, 2),
        "atr": round(atr, 4),
        "rsi": round(rsi,2) if rsi is not None else None,
        "macd": round(macd,4),
        "macd_signal": round(signal,4),
        "recommendation": rec
    }
