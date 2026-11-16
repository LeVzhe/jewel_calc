import logging
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog_app.models import Component
from app.catalog_app.repositories.component_repositories import ComponentRepository
from app.catalog_app.repositories.jewelry_repositories import JewelryRepository
from app.catalog_app.schemas.common_schemas import IdsResult
from app.catalog_app.schemas.jewelry_schemas import (
    JewelryCreate,
    JewelryListParams,
    JewelryPartInput,
    JewelryPhotoInput,
    JewelryRead,
    JewelryUpdate,
)
from app.catalog_app.services.db_errors import raise_integrity
from utils.image_utils import delete_images_by_guid, upload_images_to_r2_pipeline
from utils.image_utils.keys import jewelry_photo_folder

logger = logging.getLogger(__name__)

_PART_CONFLICT = "Component is already in this piece"


class JewelryService:
    @classmethod
    async def get_list(cls, db: AsyncSession, params: JewelryListParams):
        return await JewelryRepository.get_list(db=db, params=params)

    @classmethod
    async def get_by_id(cls, db: AsyncSession, jewelry_id: int) -> JewelryRead:
        row = await JewelryRepository.get_by_id(db=db, jewelry_id=jewelry_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Jewelry {jewelry_id} not found")
        return row

    @classmethod
    async def create(cls, db: AsyncSession, data: JewelryCreate) -> JewelryRead:
        components = await cls._load_components(
            db,
            [part.component_id for part in data.parts],
            already_used=set(),
        )
        jewelry_guid = uuid4()
        folder = jewelry_photo_folder(jewelry_guid)
        uploaded: list[UUID] = []
        photos: list[dict] = []
        try:
            for raw in data.photos:
                photo_guid = uuid4()
                fields = await upload_images_to_r2_pipeline(
                    image_base64=raw,
                    guid=photo_guid,
                    r2_folder=folder,
                )
                uploaded.append(photo_guid)
                photos.append({"guid": photo_guid, **fields})
        except Exception:
            await cls._cleanup(uploaded, folder)
            raise
        try:
            created = await JewelryRepository.create(
                db=db,
                data={
                    "guid": jewelry_guid,
                    "name": data.name,
                    "sale_price": data.sale_price,
                    "parts": cls._part_payload(data.parts, components, previous={}),
                    "photos": photos,
                },
            )
        except IntegrityError as error:
            await cls._cleanup(uploaded, folder)
            raise_integrity(error, constraint="uq_jewelry_part_component", conflict_detail=_PART_CONFLICT)
        logger.info("Jewelry [%s:%s] was created.", created.id, created.name)
        return created

    @classmethod
    async def update(cls, db: AsyncSession, jewelry_id: int, data: JewelryUpdate) -> JewelryRead:
        current = await cls.get_by_id(db, jewelry_id)
        fields = data.model_fields_set
        if not fields:
            return current

        parts_payload = None
        if "parts" in fields and data.parts is not None:
            already_used = {part.component_id for part in current.parts}
            components = await cls._load_components(
                db,
                [part.component_id for part in data.parts],
                already_used=already_used,
            )
            previous = {part.component_id: part.unit_cost for part in current.parts}
            parts_payload = cls._part_payload(data.parts, components, previous=previous)

        photo_specs = None
        uploaded: list[UUID] = []
        removed: list[UUID] = []
        folder = jewelry_photo_folder(current.guid)
        if "photos" in fields and data.photos is not None:
            photo_specs, uploaded, removed = await cls._prepare_photos(current, data.photos, folder)

        try:
            updated = await JewelryRepository.update(
                db=db,
                jewelry_id=jewelry_id,
                name=data.name if "name" in fields else None,
                parts=parts_payload,
                photos=photo_specs,
                sale_price=data.sale_price if "sale_price" in fields else None,
            )
        except IntegrityError as error:
            await cls._cleanup(uploaded, folder)
            raise_integrity(error, constraint="uq_jewelry_part_component", conflict_detail=_PART_CONFLICT)
        if updated is None:
            await cls._cleanup(uploaded, folder)
            raise HTTPException(status_code=404, detail=f"Jewelry {jewelry_id} not found")
        await cls._cleanup(removed, folder)
        logger.info("Jewelry [%s:%s] was updated.", updated.id, updated.name)
        return updated

    @classmethod
    async def archive(cls, db: AsyncSession, ids: list[int]) -> IdsResult:
        result = await JewelryRepository.set_archived(db=db, ids=ids, archived=True)
        logger.info("Jewelry archived: %s", result.ids)
        return result

    @classmethod
    async def unarchive(cls, db: AsyncSession, ids: list[int]) -> IdsResult:
        result = await JewelryRepository.set_archived(db=db, ids=ids, archived=False)
        logger.info("Jewelry restored: %s", result.ids)
        return result

    @classmethod
    async def _load_components(
        cls,
        db: AsyncSession,
        component_ids: list[int],
        *,
        already_used: set[int],
    ) -> dict[int, Component]:
        if len(component_ids) != len(set(component_ids)):
            raise HTTPException(status_code=400, detail=_PART_CONFLICT)
        rows = await ComponentRepository.get_rows_by_ids(db, component_ids)
        for component_id in component_ids:
            row = rows.get(component_id)
            if row is None:
                raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
            if row.is_archived and component_id not in already_used:
                raise HTTPException(status_code=400, detail=f"Component {component_id} is archived")
        return rows

    @classmethod
    def _part_payload(
        cls,
        parts: list[JewelryPartInput],
        components: dict[int, Component],
        *,
        previous: dict[int, float],
    ) -> list[dict]:
        payload = []
        for part in parts:
            component = components[part.component_id]
            payload.append(
                {
                    "component_id": part.component_id,
                    "quantity": part.quantity,
                    "unit_cost": previous.get(part.component_id, component.cost),
                }
            )
        return payload

    @classmethod
    async def _prepare_photos(
        cls,
        current: JewelryRead,
        photos: list[JewelryPhotoInput],
        folder: str,
    ) -> tuple[list[dict], list[UUID], list[UUID]]:
        known = {photo.id: photo.guid for photo in current.photos}
        seen: set[int] = set()
        for item in photos:
            if item.id is None:
                continue
            if item.id in seen:
                raise HTTPException(status_code=400, detail="Photo is listed twice")
            if item.id not in known:
                raise HTTPException(status_code=400, detail=f"Photo {item.id} is not on this piece")
            seen.add(item.id)

        specs: list[dict] = []
        uploaded: list[UUID] = []
        try:
            for item in photos:
                if item.id is not None:
                    specs.append({"keep_id": item.id})
                    continue
                photo_guid = uuid4()
                fields = await upload_images_to_r2_pipeline(
                    image_base64=item.image_base64 or "",
                    guid=photo_guid,
                    r2_folder=folder,
                )
                uploaded.append(photo_guid)
                specs.append({"guid": photo_guid, **fields})
        except Exception:
            await cls._cleanup(uploaded, folder)
            raise
        removed = [guid for photo_id, guid in known.items() if photo_id not in seen]
        return specs, uploaded, removed

    @classmethod
    async def _cleanup(cls, photo_guids: list[UUID], folder: str) -> None:
        for photo_guid in photo_guids:
            await delete_images_by_guid(photo_guid, folder)
