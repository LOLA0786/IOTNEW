from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.prod_api.routers import techdebt
from apps.prod_api.routers.ioa import router as ioa_router

app = FastAPI(title="PrivateVault Production API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "✅ PrivateVault Production API Live"}

# Existing TechDebt router
app.include_router(techdebt.router, prefix="/techdebt", tags=["Tech Debt"])

# IOA router
app.include_router(ioa_router, tags=["IOA"])
