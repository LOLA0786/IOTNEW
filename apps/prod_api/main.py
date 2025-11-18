from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.prod_api.routers.ioa import router as ioa_router

app = FastAPI(title="PrivateVault IOA API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "IOA API Live"}


app.include_router(ioa_router)
