from fastapi import APIRouter
from pydantic import BaseModel
import yfinance as yf, numpy as np
from apps.prod_api.routers.ioa import grok_score
from apps.prod_api.broker_sim import append_line
router = APIRouter(prefix="/strategy", tags=["Strategy"])

class StratReq(BaseModel):
    strategy: str
    symbol: str
    params: dict | None = None

@router.post("/run")
def run_strategy(req: StratReq):
    s = req.symbol
    strat = req.strategy.lower()
    price = float(yf.Ticker(s).history(period="5d", interval="1m")["Close"].iloc[-1])
    # Momentum simple: compare last vs 30-min MA
    hist = yf.Ticker(s).history(period="1d", interval="1m")["Close"]
    ma30 = float(hist[-30:].mean()) if len(hist)>=30 else float(hist.mean())
    if strat=="momentum":
        if price > ma30:
            decision = "buy"
        else:
            decision = "hold"
    elif strat=="mean-reversion":
        if price < ma30:
            decision = "buy"
        else:
            decision = "sell"
    else:
        decision = "hold"
    return {"symbol":s,"strategy":strat,"price":price,"decision":decision, "ma30":ma30}
