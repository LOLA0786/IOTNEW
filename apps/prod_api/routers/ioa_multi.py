import json
import yfinance as yf
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from apps.prod_api.grok_client import call_grok_prompt

router = APIRouter()


class MultiRunRequest(BaseModel):
    symbols: List[str]


@router.post("/run")
def run_multi(req: MultiRunRequest):
    results = []

    for sym in req.symbols:
        symbol = sym.upper()

        # 1. Fetch price
        data = yf.Ticker(symbol).history(period="1d", interval="1m")
        if data.empty:
            results.append(
                {"symbol": symbol, "status": "error", "message": "No market data found"}
            )
            continue

        price = float(data["Close"].iloc[-1])

        # 2. Grok JSON scoring
        prompt = f"""
        Evaluate {symbol} at price {price}.
        Return JSON only:
        {{
          "sentiment": "...",
          "reason": "...",
          "score": 0-100
        }}
        """

        grok = call_grok_prompt(prompt)

        if not grok["ok"]:
            results.append(
                {
                    "symbol": symbol,
                    "price": price,
                    "status": "error",
                    "message": grok["error"],
                }
            )
            continue

        try:
            parsed = json.loads(grok["text"])
        except:
            parsed = {"sentiment": "neutral", "reason": "parse_error", "score": 50}

        score = float(parsed.get("score", 0))
        boosted = score * 1.5
        saved = boosted >= 78

        results.append(
            {
                "symbol": symbol,
                "status": "ok",
                "price": price,
                "sentiment": parsed.get("sentiment"),
                "reason": parsed.get("reason"),
                "score": score,
                "boosted_score": boosted,
                "decision": "saved" if saved else "ignored",
                "saved": saved,
            }
        )

    return {"status": "ok", "count": len(results), "results": results}
