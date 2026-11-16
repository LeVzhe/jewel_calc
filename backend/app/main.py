import logging
from contextlib import asynccontextmanager
from datetime import datetime

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
    summary="Каталог комплектующих и готовых изделий для домашнего калькулятора",
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
    catalog_controllers.JewelryController(),
):
    app.include_router(controller.router)


@app.get("/", tags=["Meta"])
async def root():
    return {"name": "jewel_calc", "docs": "/docs", "health": "/health"}


@app.get("/meta", tags=["Meta"])
async def get_meta():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "year": datetime.now().year,
        "author": settings.app_author,
    }


@app.get("/health", tags=["Meta"])
async def health(db: DbSession):
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Database healthcheck failed")
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok"}
