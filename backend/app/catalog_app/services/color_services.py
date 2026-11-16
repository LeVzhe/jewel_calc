import logging

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.catalog_app.repositories.color_repositories import ColorRepository
from app.catalog_app.schemas.color_schemas import ColorCreate, ColorRead, ColorUpdate
from app.catalog_app.schemas.common_schemas import IdsResult, ListParams
from app.catalog_app.services.db_errors import raise_integrity

logger = logging.getLogger(__name__)


class ColorService:
    @classmethod
    async def get_list(cls, db, params: ListParams) -> list[ColorRead]:
        return await ColorRepository.get_list(db=db, params=params)

    @classmethod
    async def get_by_id(cls, db, color_id: int) -> ColorRead:
        row = await ColorRepository.get_by_id(db=db, color_id=color_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Color {color_id} not found")
        return row

    @classmethod
    async def create(cls, db, data: ColorCreate) -> ColorRead:
        try:
            created = await ColorRepository.create(db=db, name=data.name)
        except IntegrityError as error:
            raise_integrity(
                error,
                constraint="uq_color_name_lower",
                conflict_detail="Color with this name already exists",
            )
        logger.info("Color [%s:%s] was created.", created.id, created.name)
        return created

    @classmethod
    async def update(cls, db, color_id: int, data: ColorUpdate) -> ColorRead:
        current = await cls.get_by_id(db, color_id)
        if data.name is None:
            return current
        try:
            updated = await ColorRepository.update_name(db=db, color_id=color_id, name=data.name)
        except IntegrityError as error:
            raise_integrity(
                error,
                constraint="uq_color_name_lower",
                conflict_detail="Color with this name already exists",
            )
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Color {color_id} not found")
        logger.info("Color [%s:%s] was updated.", updated.id, updated.name)
        return updated

    @classmethod
    async def archive(cls, db, ids: list[int]) -> IdsResult:
        result = await ColorRepository.set_archived(db=db, ids=ids, archived=True)
        logger.info("Colors archived: %s", result.ids)
        return result

    @classmethod
    async def unarchive(cls, db, ids: list[int]) -> IdsResult:
        result = await ColorRepository.set_archived(db=db, ids=ids, archived=False)
        logger.info("Colors restored: %s", result.ids)
        return result
