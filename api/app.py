from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.middleware import APIKeyMiddleware
from api.routes.analyze import router as analyze_router
from api.routes.compare import router as compare_router
from api.routes.health import router as health_router

app = FastAPI(title="Legal AI Assistant", version="0.1.0")
app.add_middleware(APIKeyMiddleware)
app.include_router(health_router)
app.include_router(analyze_router)
app.include_router(compare_router)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
