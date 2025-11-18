from fastapi import APIRouter
from pydantic import BaseModel
import yfinance as yf
from apps.prod_api.grok_client import call_grok_prompt

router = APIRouter(prefix="/news", tags=["News"])

class NewsReq(BaseModel):
    symbol: str = "AAPL"
    top: int = 3

@router.post("/scan")
def scan_news(req: NewsReq):
    t = yf.Ticker(req.symbol)
    # yfinance may provide .news
    news = getattr(t, "news", None)
    headlines = []
    if isinstance(news, list) and news:
        for n in news[:req.top]:
            headlines.append(n.get("title") or n.get("headline") or str(n))
    else:
        # fallback: use short company summary
        info = t.info if hasattr(t, "info") else {}
        headlines.append(info.get("longBusinessSummary","No news found")[:240])
    # Combine headlines and ask Grok for sentiment
    prompt = "Given these headlines, provide sentiment("+req.symbol+") as JSON {sentiment,reason,impact}\n\n" + "\\n".join(headlines)
    res = call_grok_prompt(prompt)
    return {"headlines": headlines, "grok": res}
