from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.companies import router as companies_router
from app.routers.marketing import router as marketing_router
from app.routers.runs import router as runs_router

app = FastAPI(title="GTM Agent API", version="0.1.0")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(runs_router)
app.include_router(companies_router)
app.include_router(marketing_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
