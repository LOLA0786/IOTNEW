from fastapi import APIRouter
from pydantic import BaseModel
import json, os, yfinance as yf
from openai import OpenAI

router = APIRouter()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

class RunRequest(BaseModel):
    symbol: str = "AAPL"
    session_id: str | None = None


def fetch_price(symbol: str):
    data = yf.Ticker(symbol).history(period="1d", interval="1m")
    if data.empty:
        return None
    return float(data["Close"].iloc[-1])


def get_gpt_score(symbol: str, price: float):
    """GPT returns structured JSON: sentiment + score"""
    prompt = f"""
You are an autonomous trading evaluator.

Given:
Symbol: {symbol}
Price: {price}

Return STRICT JSON ONLY:
{{
  "sentiment": "bullish" or "bearish" or "neutral",
  "reason": "very short reason",
  "score": NUMBER_FROM_0_TO_100
}}

Score rules:
- Bullish → 50–90
- Bearish → 10–50
- Neutral → 40–60
- NEVER output text outside JSON.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Return only JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        raw = response.choices[0].message.content.strip()

        # Parse JSON safely
        try:
            data = json.loads(raw)
            return data
        except:
            return {"sentiment": "neutral", "reason": raw, "score": 50}

    except Exception as e:
        return {"sentiment": "error", "reason": str(e), "score": 0}


@router.post("/run")
def run_pipeline(req: RunRequest):

    # 1️⃣ PRODUCER
    price = fetch_price(req.symbol)

    # 2️⃣ GPT → structured scoring
    gpt = get_gpt_score(req.symbol, price)
    score = float(gpt.get("score", 0))

    # 3️⃣ CONSUMER (boost)
    boosted = score * 1.5
    decision = "ignored"
    saved = False

    if boosted >= 78:
        decision = "saved"
        saved = True
        with open("/tmp/ioa_saved.jsonl", "a") as f:
            f.write(json.dumps({"symbol": req.symbol, "score": boosted}) + "\\n")

    # 4️⃣ LOGGER
    with open("/tmp/ioa_logs.txt", "a") as f:
        f.write(json.dumps({
            "symbol": req.symbol,
            "price": price,
            "sentiment": gpt.get("sentiment"),
            "reason": gpt.get("reason"),
            "score": score,
            "boosted": boosted,
            "decision": decision
        }) + "\\n")

    return {
        "status": "ok",
        "price": price,
        "sentiment": gpt.get("sentiment"),
        "reason": gpt.get("reason"),
        "score": score,
        "boosted_score": boosted,
        "decision": decision,
        "saved": saved
    }
