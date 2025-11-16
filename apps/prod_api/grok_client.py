import os
import requests
import time
from typing import Dict, Any

# === ENV VARS ===
GROK_API_KEY = os.getenv("GROK_API_KEY", "")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4-latest")

# xAI Grok URLs (will try fallback URLs automatically)
GROK_ENDPOINTS = [
    "https://api.x.ai/v1/chat/completions",
    "https://api.x.ai/chat/completions",
    "https://api.x.ai/v1/messages"
]

# IMPORTANT: xAI India region works best with x-api-key header
HEADERS = {
    "x-api-key": GROK_API_KEY,
    "Content-Type": "application/json"
}


def call_grok_prompt(prompt: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Calls xAI Grok chat completions using safe retries, multi-endpoint fallback,
    and robust JSON extraction.

    Returns:
      { "ok": bool, "text": str|None, "error": str|None, "raw": object }
    """
    if not GROK_API_KEY:
        return {"ok": False, "error": "GROK_API_KEY not set", "text": None, "raw": None}

    payload = {
        "model": GROK_MODEL,
        "messages": [
            {"role": "system", "content": "You are a trading assistant. Return JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "max_tokens": 300
    }

    last_error = None

    # Try each Grok endpoint
    for url in GROK_ENDPOINTS:
        # Try each endpoint up to 3 times
        for attempt in range(3):
            try:
                r = requests.post(url, json=payload, headers=HEADERS, timeout=timeout)

                # Success
                if r.status_code == 200:
                    try:
                        data = r.json()
                    except Exception:
                        return {"ok": False, "error": "Invalid JSON", "text": r.text, "raw": r.text}

                    # Extract text safely (xAI sometimes uses OpenAI-like structure)
                    text = None

                    # OpenAI-like response
                    if isinstance(data.get("choices"), list) and data["choices"]:
                        ch = data["choices"][0]
                        if isinstance(ch.get("message"), dict) and "content" in ch["message"]:
                            text = ch["message"]["content"]
                        elif "text" in ch:
                            text = ch["text"]

                    # Fallback to full body text
                    if not text:
                        text = data.get("text") or str(data)

                    return {"ok": True, "text": text, "error": None, "raw": data}

                # If auth error → don’t retry
                if r.status_code in (401, 403):
                    return {"ok": False, "error": f"Auth error: {r.text}", "text": None, "raw": r.text}

                last_error = f"HTTP {r.status_code}: {r.text}"

            except requests.exceptions.Timeout:
                last_error = "Timeout"
            except Exception as e:
                last_error = str(e)

            time.sleep(0.5)  # small backoff

    # If all endpoints failed:
    return {"ok": False, "error": last_error or "Unknown error", "text": None, "raw": None}
