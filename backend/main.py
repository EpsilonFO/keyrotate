import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import require_auth
from config import settings
from db import init_db
from routes import auth as auth_routes
from routes import keys as keys_routes
from routes import rotate as rotate_routes
from scheduler import run_daily_check, start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("keyrotate")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler = start_scheduler()
    logger.info("KeyRotate started. Frontend at %s", settings.app_base_url)
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="KeyRotate", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_base_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(keys_routes.router)
app.include_router(rotate_routes.router)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/_run_check", dependencies=[Depends(require_auth)])
def manual_check() -> dict:
    """Trigger the daily check manually — handy to test the email pipeline."""
    run_daily_check()
    return {"ok": True}
