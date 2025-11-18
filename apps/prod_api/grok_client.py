import os
import json
import base64
import requests
from dotenv import load_dotenv

load_dotenv()


def decode_key(name):
    val = os.getenv(name, "")
    if not val:
        return None
    try:
        return base64.b64decode(val).decode()
    except Exception:
        return None


GROK_KEY = decode_key("GROK_API_KEY_B64")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4-latest")

XAI_URL = "https://api.x.ai/v1/chat/completions"


def call_grok_prompt(prompt: str):
    if not GROK_KEY:
        return {"ok": False, "error": "Missing Grok API Key", "text": None, "raw": None}

    try:
        resp = requests.post(
            XAI_URL,
            headers={
                "Authorization": f"Bearer {GROK_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROK_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an analytical agent. Return JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
            },
            timeout=20,
        )

        raw = resp.json()
        if "choices" not in raw:
            return {"ok": False, "error": str(raw), "text": None, "raw": raw}

        text = raw["choices"][0]["message"]["content"]
        return {"ok": True, "error": None, "text": text, "raw": raw}

    except Exception as e:
        return {"ok": False, "error": str(e), "text": None, "raw": None}
