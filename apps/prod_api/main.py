from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from apps.prod_api.routers import techdebt
from apps.prod_api.routers.ioa import router as ioa_router
from apps.prod_api.routers.ioa_multi import router as ioa_multi_router
from apps.prod_api.routers.stream import router as stream_router
from apps.prod_api.routers.risk import router as risk_router
from apps.prod_api.routers.risk_adv import router as risk_adv_router
from apps.prod_api.routers.ws import router as ws_router
from apps.prod_api.broker_sim import router as broker_router

# New routers
from apps.prod_api.routers.portfolio import router as portfolio_router
from apps.prod_api.routers.strategy import router as strategy_router
from apps.prod_api.routers.candles import router as candles_router
from apps.prod_api.routers.news_agent import router as news_router
from apps.prod_api.routers.reasoner import router as reason_router
from apps.prod_api.routers.pnl import router as pnl_router

app = FastAPI(title="PrivateVault Production API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")

@app.get("/")
def root():
    return {"status":"ok"}

# include routers
app.include_router(techdebt.router, prefix="/techdebt")
app.include_router(ioa_router)
app.include_router(ioa_multi_router)
app.include_router(stream_router)
app.include_router(risk_router)
app.include_router(risk_adv_router)
app.include_router(ws_router)
app.include_router(broker_router)

# new
app.include_router(portfolio_router)
app.include_router(strategy_router)
app.include_router(candles_router)
app.include_router(news_router)
app.include_router(reason_router)
app.include_router(pnl_router)
