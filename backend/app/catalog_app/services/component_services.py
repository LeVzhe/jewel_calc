import logging
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.catalog_app.repositories.component_repositories import ComponentRepository
from app.catalog_app.schemas.common_schemas import IdsResult
from app.catalog_app.schemas.component_schemas import (
    ComponentCreate,
    ComponentListParams,
    ComponentRead,
    ComponentUpdate,
)
from app.catalog_app.services.color_services import ColorService
from app.catalog_app.services.component_type_services import ComponentTypeService
from app.catalog_app.services.db_errors import raise_integrity
from utils.constants import ComponentUnit, R2Folders
from utils.image_utils import delete_images_by_guid, upload_images_to_r2_pipeline

logger = logging.getLogger(__name__)

_NAME_CONFLICT = "Component with this name already exists in this type"


class ComponentService:
    @classmethod
    async def _ensure_type(cls, db, type_id: int) -> None:
        row = await ComponentTypeService.get_by_id(db, type_id)
        if row.is_archived:
            raise HTTPException(status_code=400, detail=f"Component type {type_id} is archived")

    @classmethod
    async def _ensure_color(cls, db, color_id: int) -> None:
        row = await ColorService.get_by_id(db, color_id)
        if row.is_archived:
            raise HTTPException(status_code=400, detail=f"Color {color_id} is archived")

    @classmethod
    async def get_list(cls, db, params: ComponentListParams):
        return await ComponentRepository.get_list(db=db, params=params)

    @classmethod
    async def get_by_id(cls, db, component_id: int) -> ComponentRead:
        row = await ComponentRepository.get_by_id(db=db, component_id=component_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
        return row

    @classmethod
    async def create(cls, db, data: ComponentCreate) -> ComponentRead:
        await cls._ensure_type(db, data.type_id)
        if data.color_id is not None:
            await cls._ensure_color(db, data.color_id)

        guid = uuid4()
        image_fields = await upload_images_to_r2_pipeline(
            image_base64=data.image_base64,
            guid=guid,
            r2_folder=R2Folders.COMPONENT,
        )
        payload = {
            "guid": guid,
            "name": data.name,
            "cost": data.cost,
            "unit": data.unit.value,
            "article": data.article,
            "type_id": data.type_id,
            "color_id": data.color_id,
            "shops": data.shops,
            **image_fields,
        }
        try:
            created = await ComponentRepository.create(db=db, data=payload)
        except IntegrityError as error:
            await delete_images_by_guid(guid, R2Folders.COMPONENT)
            raise_integrity(error, constraint="uq_component_active_name_per_type", conflict_detail=_NAME_CONFLICT)
        logger.info("Component [%s:%s] was created.", created.id, created.name)
        return created

    @classmethod
    async def update(cls, db, component_id: int, data: ComponentUpdate) -> ComponentRead:
        current = await cls.get_by_id(db, component_id)
        fields = data.model_fields_set
        if "type_id" in fields and data.type_id is not None and data.type_id != current.type_id:
            await cls._ensure_type(db, data.type_id)
        if "color_id" in fields and data.color_id is not None and data.color_id != current.color_id:
            await cls._ensure_color(db, data.color_id)

        payload = data.model_dump(exclude_unset=True, exclude={"image_base64", "shops"})
        if isinstance(payload.get("unit"), ComponentUnit):
            payload["unit"] = payload["unit"].value
        if "image_base64" in fields and data.image_base64:
            image_fields = await upload_images_to_r2_pipeline(
                image_base64=data.image_base64,
                guid=current.guid,
                r2_folder=R2Folders.COMPONENT,
            )
            payload.update(image_fields)
        if not payload and "shops" not in fields:
            return current

        shops = data.shops if "shops" in fields else None
        try:
            updated = await ComponentRepository.update(
                db=db,
                component_id=component_id,
                data=payload,
                shops=shops,
            )
        except IntegrityError as error:
            raise_integrity(error, constraint="uq_component_active_name_per_type", conflict_detail=_NAME_CONFLICT)
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
        logger.info("Component [%s:%s] was updated.", updated.id, updated.name)
        return updated

    @classmethod
    async def archive(cls, db, ids: list[int]) -> IdsResult:
        result = await ComponentRepository.set_archived(db=db, ids=ids, archived=True)
        logger.info("Components archived: %s", result.ids)
        return result

    @classmethod
    async def unarchive(cls, db, ids: list[int]) -> IdsResult:
        try:
            result = await ComponentRepository.set_archived(db=db, ids=ids, archived=False)
        except IntegrityError as error:
            raise_integrity(error, constraint="uq_component_active_name_per_type", conflict_detail=_NAME_CONFLICT)
        logger.info("Components restored: %s", result.ids)
        return result
