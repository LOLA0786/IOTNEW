from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json, yfinance as yf
from apps.prod_api.routers.ioa import grok_score, openai_score, fetch_price
from apps.prod_api.publisher import publish_event

router = APIRouter(prefix="/run-multi", tags=["IOA Multi"])

class MultiReq(BaseModel):
    symbols: list[str]
    session_id: str | None = None


@router.post("/")
async def run_multi(req: MultiReq):
    results = []

    for sym in req.symbols:
        price = fetch_price(sym)
        if price is None:
            results.append({
                "symbol": sym,
                "error": "no_price"
            })
            continue

        # --- GROK FIRST ---
        g = grok_score(sym, price)

        # --- FALLBACK ---
        final = g
        if final.get("sentiment") == "error" or final.get("score", 0) <= 0:
            final = openai_score(sym, price)

        score = float(final.get("score", 0))
        boosted = score * 1.5

        decision = "ignored"
        saved = False

        record = {
            "symbol": sym,
            "price": price,
            "sentiment": final.get("sentiment"),
            "reason": final.get("reason"),
            "score": score,
            "boosted": boosted
        }

        if boosted >= 78:
            decision = "saved"
            saved = True
            with open("/tmp/ioa_saved.jsonl", "a") as f:
                f.write(json.dumps({**record, "decision": decision}) + "\n")

        # Log
        with open("/tmp/ioa_logs.txt", "a") as f:
            f.write(json.dumps({**record, "decision": decision}) + "\n")

        # Push to WebSocket
        try:
            await publish_event({**record, "decision": decision})
        except Exception:
            pass

        results.append({
            **record,
            "decision": decision,
            "saved": saved
        })

    return {
        "status": "ok",
        "count": len(results),
        "results": results
    }
