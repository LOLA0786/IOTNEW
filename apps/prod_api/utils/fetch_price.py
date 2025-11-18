import yfinance as yf
from typing import Optional

# Auto-detect global / NSE / BSE
SUFFIXES = ["", ".NS", ".BO"]


def fetch_stock_price(symbol: str) -> Optional[float]:
    """
    Attempts: SYMBOL → SYMBOL.NS → SYMBOL.BO
    Returns latest price or None.
    """
    for suffix in SUFFIXES:
        ticker = f"{symbol}{suffix}"
        try:
            data = yf.Ticker(ticker).history(period="1d", interval="1m")
            if not data.empty:
                return float(data["Close"].iloc[-1])
        except Exception:
            pass
    return None
