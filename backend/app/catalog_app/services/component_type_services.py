import logging

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.catalog_app.repositories.component_type_repositories import ComponentTypeRepository
from app.catalog_app.schemas.common_schemas import IdsResult, ListParams
from app.catalog_app.schemas.component_type_schemas import (
    ComponentTypeCreate,
    ComponentTypeRead,
    ComponentTypeUpdate,
)
from app.catalog_app.services.db_errors import raise_integrity

logger = logging.getLogger(__name__)


class ComponentTypeService:
    @classmethod
    async def get_list(cls, db, params: ListParams) -> list[ComponentTypeRead]:
        return await ComponentTypeRepository.get_list(db=db, params=params)

    @classmethod
    async def get_by_id(cls, db, type_id: int) -> ComponentTypeRead:
        row = await ComponentTypeRepository.get_by_id(db=db, type_id=type_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Component type {type_id} not found")
        return row

    @classmethod
    async def create(cls, db, data: ComponentTypeCreate) -> ComponentTypeRead:
        parent = await cls.get_by_id(db, data.parent_id)
        if parent.parent_id is not None or not parent.is_system:
            raise HTTPException(status_code=400, detail="Parent must be a root type")
        if parent.is_archived:
            raise HTTPException(status_code=400, detail="Parent type is archived")
        try:
            created = await ComponentTypeRepository.create(db=db, name=data.name, parent_id=data.parent_id)
        except IntegrityError as error:
            raise_integrity(
                error,
                constraint="uq_component_type_child_name",
                conflict_detail="Component type with this name already exists under the parent",
            )
        logger.info("Component type [%s:%s] was created.", created.id, created.name)
        return created

    @classmethod
    async def update(cls, db, type_id: int, data: ComponentTypeUpdate) -> ComponentTypeRead:
        current = await cls.get_by_id(db, type_id)
        if data.name is None:
            return current
        if current.is_system and data.name != current.name:
            raise HTTPException(status_code=400, detail="System type name is fixed")
        try:
            updated = await ComponentTypeRepository.update_name(db=db, type_id=type_id, name=data.name)
        except IntegrityError as error:
            raise_integrity(
                error,
                constraint="uq_component_type_child_name",
                conflict_detail="Component type with this name already exists under the parent",
            )
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Component type {type_id} not found")
        logger.info("Component type [%s:%s] was updated.", updated.id, updated.name)
        return updated

    @classmethod
    async def archive(cls, db, ids: list[int]) -> IdsResult:
        result = await ComponentTypeRepository.set_archived(db=db, ids=ids, archived=True)
        logger.info("Component types archived: %s", result.ids)
        return result

    @classmethod
    async def unarchive(cls, db, ids: list[int]) -> IdsResult:
        result = await ComponentTypeRepository.set_archived(db=db, ids=ids, archived=False)
        logger.info("Component types restored: %s", result.ids)
        return result
