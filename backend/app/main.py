from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db
from app.api import analyze, signals, settings as settings_api, watchlist, history
from app.scheduler.jobs import start_scheduler, shutdown_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    log.info("Investment Agent started")
    yield
    shutdown_scheduler()
    log.info("Investment Agent stopped")


app = FastAPI(title="My Investment Agent", version="0.1.0", lifespan=lifespan)

cfg = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[cfg.frontend_origin, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])


@app.get("/health")
async def health():
    return {"status": "ok"}
