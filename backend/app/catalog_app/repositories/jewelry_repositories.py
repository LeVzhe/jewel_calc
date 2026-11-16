from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.catalog_app.models import Component, Jewelry, JewelryPart, JewelryPhoto
from app.catalog_app.schemas.common_schemas import IdSkip, IdsResult
from app.catalog_app.schemas.jewelry_schemas import JewelryList, JewelryListParams, JewelryRead
from utils.constants import SkipReason
from utils.text import like_contains, utcnow


_JEWELRY_LOAD = (
    selectinload(Jewelry.photos),
    selectinload(Jewelry.parts)
    .selectinload(JewelryPart.component)
    .selectinload(Component.component_type),
    selectinload(Jewelry.parts).selectinload(JewelryPart.component).selectinload(Component.color),
)


class JewelryRepository:
    @classmethod
    async def _get_row(cls, db: AsyncSession, jewelry_id: int) -> Jewelry | None:
        stmt = (
            select(Jewelry)
            .where(Jewelry.id == jewelry_id)
            .options(*_JEWELRY_LOAD)
            .execution_options(populate_existing=True)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_id(cls, db: AsyncSession, jewelry_id: int) -> JewelryRead | None:
        row = await cls._get_row(db, jewelry_id)
        if row is None:
            return None
        return JewelryRead.model_validate(row)

    @classmethod
    def _filters(cls, params: JewelryListParams) -> list:
        filters = []
        if not params.include_archived:
            filters.append(Jewelry.is_archived.is_(False))
        if params.search:
            filters.append(Jewelry.name_key.like(like_contains(params.search.casefold()), escape="\\"))
        return filters

    @classmethod
    async def get_list(cls, db: AsyncSession, params: JewelryListParams) -> JewelryList:
        filters = cls._filters(params)
        total = await db.scalar(select(func.count()).select_from(Jewelry).where(*filters))
        stmt = (
            select(Jewelry)
            .options(*_JEWELRY_LOAD)
            .where(*filters)
            .order_by(Jewelry.updated_at.desc(), Jewelry.id.desc())
            .offset(params.skip)
            .limit(params.limit)
        )
        result = await db.execute(stmt)
        items = [JewelryRead.model_validate(row) for row in result.scalars().all()]
        return JewelryList(items=items, total=int(total or 0))

    @classmethod
    async def create(cls, db: AsyncSession, data: dict) -> JewelryRead:
        jewelry = Jewelry(
            guid=data["guid"],
            name=data["name"],
            name_key=data["name"].casefold(),
            sale_price=data["sale_price"],
        )
        jewelry.parts = [
            JewelryPart(
                component_id=item["component_id"],
                quantity=item["quantity"],
                unit_cost=item["unit_cost"],
                position=index,
            )
            for index, item in enumerate(data["parts"])
        ]
        jewelry.photos = [
            JewelryPhoto(
                guid=item["guid"],
                position=index,
                image=item["image"],
                image_preview=item["image_preview"],
                image_on_s3=item["image_on_s3"],
                image_preview_on_s3=item["image_preview_on_s3"],
            )
            for index, item in enumerate(data["photos"])
        ]
        db.add(jewelry)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise
        jewelry_id = jewelry.id
        db.expire_all()
        created = await cls.get_by_id(db, jewelry_id)
        if created is None:
            raise RuntimeError("Jewelry disappeared after save")
        return created

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        jewelry_id: int,
        *,
        name: str | None,
        parts: list[dict] | None,
        photos: list[dict] | None,
        sale_price: float | None,
    ) -> JewelryRead | None:
        row = await cls._get_row(db, jewelry_id)
        if row is None:
            return None
        if sale_price is not None:
            row.sale_price = sale_price
        if name is not None:
            row.name = name
            row.name_key = name.casefold()
        if parts is not None:
            await cls._replace_parts(db, row, parts)
        if photos is not None:
            await cls._replace_photos(db, row, photos)
        row.updated_at = utcnow()
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise
        saved_id = row.id
        db.expire_all()
        return await cls.get_by_id(db, saved_id)

    @classmethod
    async def _replace_parts(cls, db: AsyncSession, jewelry: Jewelry, parts: list[dict]) -> None:
        jewelry.parts.clear()
        await db.flush()
        for position, item in enumerate(parts):
            jewelry.parts.append(
                JewelryPart(
                    component_id=item["component_id"],
                    quantity=item["quantity"],
                    unit_cost=item["unit_cost"],
                    position=position,
                )
            )

    @classmethod
    async def _replace_photos(cls, db: AsyncSession, jewelry: Jewelry, photos: list[dict]) -> None:
        by_id = {photo.id: photo for photo in jewelry.photos}
        for photo in by_id.values():
            photo.position = photo.position + 1000
        await db.flush()
        keep_ids = {item["keep_id"] for item in photos if "keep_id" in item}
        for photo_id, photo in list(by_id.items()):
            if photo_id not in keep_ids:
                jewelry.photos.remove(photo)
        await db.flush()
        for position, item in enumerate(photos):
            if "keep_id" in item:
                by_id[item["keep_id"]].position = position
                continue
            jewelry.photos.append(
                JewelryPhoto(
                    guid=item["guid"],
                    position=position,
                    image=item["image"],
                    image_preview=item["image_preview"],
                    image_on_s3=item["image_on_s3"],
                    image_preview_on_s3=item["image_preview_on_s3"],
                )
            )

    @classmethod
    async def set_archived(cls, db: AsyncSession, ids: list[int], *, archived: bool) -> IdsResult:
        unique_ids = list(dict.fromkeys(ids))
        result = await db.execute(select(Jewelry).where(Jewelry.id.in_(unique_ids)))
        rows = {row.id: row for row in result.scalars().all()}
        changed: list[int] = []
        skipped: list[IdSkip] = []
        for item_id in unique_ids:
            row = rows.get(item_id)
            if row is None:
                skipped.append(IdSkip(id=item_id, reason=SkipReason.NOT_FOUND))
                continue
            if archived and row.is_archived:
                skipped.append(IdSkip(id=item_id, reason=SkipReason.ALREADY_ARCHIVED))
                continue
            if not archived and not row.is_archived:
                skipped.append(IdSkip(id=item_id, reason=SkipReason.ALREADY_ACTIVE))
                continue
            row.is_archived = archived
            row.updated_at = utcnow()
            changed.append(row.id)
        if changed:
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                raise
        return IdsResult(ids=changed, skipped=skipped)
