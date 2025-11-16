from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json, os, yfinance as yf
from apps.prod_api.grok_client import call_grok_prompt
from openai import OpenAI

router = APIRouter()

# Optional OpenAI fallback
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)


class RunRequest(BaseModel):
    symbol: str = "AAPL"
    session_id: str | None = None


def fetch_price(symbol: str):
    data = yf.Ticker(symbol).history(period="1d", interval="1m")
    if data.empty:
        return None
    return float(data["Close"].iloc[-1])


def parse_json(text: str):
    """Extract valid JSON from any mixed text response."""
    if not text:
        return None

    s = text.strip()

    # Remove ```json or ``` fences
    if s.startswith("```"):
        s = s.strip("`").strip()

    # Try to find JSON object boundaries
    try:
        first = s.find("{")
        last = s.rfind("}")
        if first != -1 and last != -1:
            block = s[first:last+1]
            return json.loads(block)
    except:
        pass

    # Fallback: try full string
    try:
        return json.loads(s)
    except:
        return None


def grok_score(symbol: str, price: float):
    """Primary scoring using Grok."""
    prompt = f"""
You are an autonomous trading evaluator.

Given:
Symbol: {symbol}
Price: {price}

Return STRICT JSON ONLY:

{{
  "sentiment": "bullish" | "bearish" | "neutral",
  "reason": "one-line rationale",
  "score": 0-100
}}

Rules:
- Output ONLY raw JSON.
- No explanations.
- "score" must be a NUMBER.
"""

    res = call_grok_prompt(prompt)

    if not res["ok"]:
        return {"sentiment": "error", "reason": res["error"], "score": 0, "raw": res}

    parsed = parse_json(res["text"])
    if parsed:
        try:
            parsed["score"] = float(parsed.get("score", 0))
        except:
            parsed["score"] = 0.0
        return {**parsed, "raw": parsed}

    # Fallback if JSON parsing fails
    return {"sentiment": "neutral", "reason": res["text"], "score": 50, "raw": res}


def openai_score(symbol: str, price: float):
    """Backup scoring using OpenAI."""
    if not openai_client:
        return {"sentiment": "neutral", "reason": "no_openai_key", "score": 50}

    prompt = f"""
Return ONLY JSON:
{{"sentiment":"bullish|bearish|neutral","reason":"short","score":0}}

Symbol={symbol}
Price={price}
"""

    try:
        resp = openai_client.chat.completions.create(
            model=os.getenv("AI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "Return only JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0
        )
        content = resp.choices[0].message.content
        parsed = parse_json(content)

        if parsed:
            parsed["score"] = float(parsed.get("score", 0))
            return parsed
        return {"sentiment": "neutral", "reason": content, "score": 50}
    except Exception as e:
        return {"sentiment": "error", "reason": str(e), "score": 0}


@router.post("/run")
def run_pipeline(req: RunRequest):
    price = fetch_price(req.symbol)
    if price is None:
        raise HTTPException(status_code=400, detail="price_not_found")

    # 1. Try Grok
    g = grok_score(req.symbol, price)

    # 2. Fallback to OpenAI only if Grok failed
    if g["sentiment"] == "error" or g["score"] <= 0:
        f = openai_score(req.symbol, price)
        final = f
    else:
        final = g

    score = float(final.get("score", 0))
    boosted = score * 1.5

    decision = "ignored"
    saved = False

    if boosted >= 78:
        decision = "saved"
        saved = True
        with open("/tmp/ioa_saved.jsonl", "a") as f:
            f.write(json.dumps({
                "symbol": req.symbol,
                "price": price,
                "sentiment": final["sentiment"],
                "reason": final["reason"],
                "score": score,
                "boosted": boosted
            }) + "\n")

    # Log to SSE tail file
    with open("/tmp/ioa_logs.txt", "a") as f:
        f.write(json.dumps({
            "symbol": req.symbol,
            "price": price,
            "sentiment": final["sentiment"],
            "reason": final["reason"],
            "score": score,
            "boosted": boosted,
            "decision": decision
        }) + "\n")

    return {
        "status": "ok",
        "price": price,
        "sentiment": final["sentiment"],
        "reason": final["reason"],
        "score": score,
        "boosted_score": boosted,
        "decision": decision,
        "saved": saved
    }
