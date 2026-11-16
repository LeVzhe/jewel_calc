import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.catalog_app import controllers as catalog_controllers
from app.deps import DbSession
from core.settings import settings
from utils.db_utils import DbManager
from utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    await DbManager.connect()
    yield
    await DbManager.dispose()


app = FastAPI(
    title="Jewel Calc",
    version=settings.app_version,
    summary="Каталог комплектующих для домашнего калькулятора бижутерии",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for controller in (
    catalog_controllers.ComponentTypeController(),
    catalog_controllers.ColorController(),
    catalog_controllers.ComponentController(),
):
    app.include_router(controller.router)


@app.get("/", tags=["Meta"])
async def root():
    return {"name": "jewel_calc", "docs": "/docs", "health": "/health"}


@app.get("/meta", tags=["Meta"])
async def get_meta():
    return {"app_version": settings.app_version}


@app.get("/health", tags=["Meta"])
async def health(db: DbSession):
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Database healthcheck failed")
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok"}
