import os, json
import yfinance as yf
from fastapi import APIRouter
from pydantic import BaseModel
from apps.prod_api.grok_client import call_grok_prompt
from apps.prod_api.utils.fetch_price import fetch_stock_price

router = APIRouter(prefix="/ioa", tags=["Internet of Agents"])


class RunRequest(BaseModel):
    symbol: str
    session_id: str = "live"


def grok_score(symbol: str, price: float):
    prompt = f"""
Return JSON only:
{{
  "sentiment": "",
  "reason": "",
  "score": 0-100
}}

Analyze: {symbol} at price {price}.
"""
    result = call_grok_prompt(prompt)
    if not result["ok"]:
        return {"sentiment": "neutral", "reason": result["error"], "score": 50}
    try:
        return json.loads(result["text"])
    except:
        return {"sentiment": "neutral", "reason": "parse-error", "score": 50}


def boost_score(score: float) -> float:
    return score * 1.5


def decision(final_score: float) -> str:
    return "saved" if final_score >= 78 else "ignored"


@router.post("/run")
async def run_ioa(req: RunRequest):
    price = fetch_stock_price(req.symbol)
    if price is None:
        return {"status": "error", "message": f"Could not fetch price for {req.symbol}"}

    scored = grok_score(req.symbol, price)

    boosted = boost_score(scored["score"])
    final_decision = decision(boosted)

    return {
        "status": "ok",
        "symbol": req.symbol,
        "price": price,
        "sentiment": scored["sentiment"],
        "reason": scored["reason"],
        "score": scored["score"],
        "boosted": boosted,
        "decision": final_decision,
        "saved": final_decision == "saved",
    }
