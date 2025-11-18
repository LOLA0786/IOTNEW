from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json, os, yfinance as yf
from apps.prod_api.grok_client import call_grok_prompt
from openai import OpenAI
from apps.prod_api.publisher import publish_event

router = APIRouter()

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
    if not text:
        return None
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`").strip()
    try:
        first = s.find("{")
        last = s.rfind("}")
        if first != -1 and last != -1:
            candidate = s[first:last+1]
            return json.loads(candidate)
    except:
        pass
    try:
        return json.loads(s)
    except:
        return None

def grok_score(symbol: str, price: float):
    prompt = f"""
You are an autonomous trading evaluator.
Given:
Symbol: {symbol}
Price: {price}
Return STRICT JSON ONLY:
{{"sentiment":"bullish|bearish|neutral","reason":"one-line","score":0-100}}
"""
    res = call_grok_prompt(prompt)
    if not res.get("ok"):
        return {"sentiment":"error","reason":res.get("error"), "score":0, "raw": res}
    parsed = parse_json(res.get("text",""))
    if parsed:
        try:
            parsed["score"] = float(parsed.get("score",0))
        except:
            parsed["score"] = 0
        return {**parsed, "raw": parsed}
    return {"sentiment":"neutral","reason":res.get("text",""),"score":50,"raw":res}

def openai_score(symbol: str, price: float):
    if not openai_client:
        return {"sentiment":"neutral","reason":"no_openai_key","score":50}
    prompt = f'{{"sentiment":"bullish|bearish|neutral","reason":"short","score":0}} Symbol:{symbol} Price:{price}'
    try:
        resp = openai_client.chat.completions.create(
            model=os.getenv("AI_MODEL","gpt-4o-mini"),
            messages=[{"role":"system","content":"Return only JSON."},{"role":"user","content":prompt}],
            temperature=0
        )
        content = resp.choices[0].message.content
        parsed = parse_json(content)
        if parsed:
            parsed["score"] = float(parsed.get("score",0))
            return parsed
        return {"sentiment":"neutral","reason":content,"score":50}
    except Exception as e:
        return {"sentiment":"error","reason":str(e),"score":0}

@router.post("/run")
async def run_pipeline(req: RunRequest):
    price = fetch_price(req.symbol)
    if price is None:
        raise HTTPException(status_code=400, detail="no_price")

    g = grok_score(req.symbol, price)
    if g.get("sentiment") == "error" or g.get("score",0) <= 0:
        f = openai_score(req.symbol, price)
        final = f
    else:
        final = g

    score = float(final.get("score",0))
    boosted = score * 1.5
    decision = "ignored"
    saved = False

    record = {
        "symbol": req.symbol,
        "price": price,
        "sentiment": final.get("sentiment"),
        "reason": final.get("reason"),
        "score": score,
        "boosted": boosted
    }

    if boosted >= 78:
        decision = "saved"
        saved = True
        with open("/tmp/ioa_saved.jsonl","a") as f:
            f.write(json.dumps({**record, "decision":decision}) + "\\n")

    # log
    with open("/tmp/ioa_logs.txt","a") as f:
        f.write(json.dumps({**record, "decision":decision}) + "\\n")

    # publish over websockets (non-blocking fire-and-forget)
    try:
        await publish_event({**record, "decision":decision})
    except Exception:
        pass

    return {
        "status":"ok",
        "price": price,
        "sentiment": final.get("sentiment"),
        "reason": final.get("reason"),
        "score": score,
        "boosted_score": boosted,
        "decision": decision,
        "saved": saved
    }
