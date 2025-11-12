from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.prod_api.routers import techdebt

app = FastAPI(title="PrivateVault Production API", version="1.0")

# ✅ CORS setup so it works with frontend
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

# ✅ Include routers (TechDebt etc.)
app.include_router(techdebt.router, prefix="/techdebt", tags=["Tech Debt"])


