from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apps.prod_api.routers import techdebt
from apps.prod_api.routers.ioa import router as ioa_router
from apps.prod_api.routers.ioa_multi import router as ioa_multi_router
from apps.prod_api.routers.stream import router as stream_router
from apps.prod_api.routers.risk import router as risk_router

app = FastAPI(title="PrivateVault Production API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve dashboard static
app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")

@app.get("/")
def root():
    return {"status": "✅ PrivateVault Production API Live"}

app.include_router(techdebt.router, prefix="/techdebt", tags=["Tech Debt"])
app.include_router(ioa_router, tags=["IOA"])
app.include_router(ioa_multi_router, tags=["IOA Multi"])
app.include_router(stream_router, tags=["Stream"])
app.include_router(risk_router, tags=["Risk"])
