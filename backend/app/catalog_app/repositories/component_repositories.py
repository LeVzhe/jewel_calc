from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.catalog_app.models import Component, ComponentShop
from app.catalog_app.schemas.common_schemas import IdSkip, IdsResult
from app.catalog_app.schemas.component_schemas import ComponentListParams, ComponentRead
from utils.constants import ComponentUnit, SkipReason
from utils.text import like_contains, utcnow


_COMPONENT_LOAD = (
    selectinload(Component.shops),
    selectinload(Component.component_type),
    selectinload(Component.color),
)


class ComponentRepository:
    @classmethod
    async def _get_row(cls, db: AsyncSession, component_id: int) -> Component | None:
        stmt = (
            select(Component)
            .where(Component.id == component_id)
            .options(*_COMPONENT_LOAD)
            .execution_options(populate_existing=True)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_id(cls, db: AsyncSession, component_id: int) -> ComponentRead | None:
        row = await cls._get_row(db, component_id)
        if row is None:
            return None
        return ComponentRead.model_validate(row)

    @classmethod
    async def get_list(cls, db: AsyncSession, params: ComponentListParams) -> list[ComponentRead]:
        stmt = select(Component).options(*_COMPONENT_LOAD).order_by(Component.name, Component.id)
        if not params.include_archived:
            stmt = stmt.where(Component.is_archived.is_(False))
        if params.type_id is not None:
            stmt = stmt.where(Component.type_id == params.type_id)
        if params.color_id is not None:
            stmt = stmt.where(Component.color_id == params.color_id)
        if params.search:
            stmt = stmt.where(
                Component.name_key.like(like_contains(params.search.casefold()), escape="\\")
            )
        stmt = stmt.offset(params.skip).limit(params.limit)
        result = await db.execute(stmt)
        return [ComponentRead.model_validate(row) for row in result.scalars().all()]

    @classmethod
    async def create(cls, db: AsyncSession, data: dict) -> ComponentRead:
        component = Component(
            guid=data["guid"],
            name=data["name"],
            name_key=data["name"].casefold(),
            cost=data["cost"],
            unit=data["unit"],
            article=data["article"],
            image=data["image"],
            image_preview=data["image_preview"],
            image_on_s3=data["image_on_s3"],
            image_preview_on_s3=data["image_preview_on_s3"],
            type_id=data["type_id"],
            color_id=data["color_id"],
        )
        component.shops = [
            ComponentShop(label=label, position=index) for index, label in enumerate(data["shops"])
        ]
        db.add(component)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise
        component_id = component.id
        db.expire_all()
        created = await cls.get_by_id(db, component_id)
        if created is None:
            raise RuntimeError("Component disappeared after save")
        return created

    @classmethod
    async def update(
        cls,
        db: AsyncSession,
        component_id: int,
        data: dict,
        shops: list[str] | None,
    ) -> ComponentRead | None:
        row = await cls._get_row(db, component_id)
        if row is None:
            return None
        if "name" in data:
            row.name = data["name"]
            row.name_key = data["name"].casefold()
        if "cost" in data:
            row.cost = data["cost"]
        if "unit" in data:
            unit = data["unit"]
            row.unit = unit.value if isinstance(unit, ComponentUnit) else unit
        if "article" in data:
            row.article = data["article"]
        if "type_id" in data:
            row.type_id = data["type_id"]
        if "color_id" in data:
            row.color_id = data["color_id"]
        for field in ("image", "image_preview", "image_on_s3", "image_preview_on_s3"):
            if field in data:
                setattr(row, field, data[field])
        if shops is not None:
            await cls._replace_shops(db, row, shops)
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
    async def _replace_shops(cls, db: AsyncSession, component: Component, labels: list[str]) -> None:
        component.shops.clear()
        await db.flush()
        for position, label in enumerate(labels):
            component.shops.append(ComponentShop(label=label, position=position))

    @classmethod
    async def set_archived(cls, db: AsyncSession, ids: list[int], *, archived: bool) -> IdsResult:
        unique_ids = list(dict.fromkeys(ids))
        result = await db.execute(
            select(Component).where(Component.id.in_(unique_ids)).options(*_COMPONENT_LOAD)
        )
        rows = {row.id: row for row in result.scalars().all()}
        changed: list[int] = []
        skipped: list[IdSkip] = []
        for item_id in unique_ids:
            row = rows.get(item_id)
            if row is None:
                skipped.append(IdSkip(id=item_id, reason=SkipReason.NOT_FOUND))
                continue
            if archived:
                if row.is_archived:
                    skipped.append(IdSkip(id=item_id, reason=SkipReason.ALREADY_ARCHIVED))
                    continue
                row.is_archived = True
            else:
                if not row.is_archived:
                    skipped.append(IdSkip(id=item_id, reason=SkipReason.ALREADY_ACTIVE))
                    continue
                if row.component_type.is_archived:
                    skipped.append(IdSkip(id=item_id, reason=SkipReason.TYPE_ARCHIVED))
                    continue
                taken = await db.execute(
                    select(Component.id).where(
                        Component.type_id == row.type_id,
                        Component.name_key == row.name_key,
                        Component.is_archived.is_(False),
                        Component.id != row.id,
                    )
                )
                if taken.scalar_one_or_none() is not None:
                    skipped.append(IdSkip(id=item_id, reason=SkipReason.NAME_TAKEN))
                    continue
                row.is_archived = False
            row.updated_at = utcnow()
            changed.append(row.id)

        if changed:
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                raise
        return IdsResult(ids=changed, skipped=skipped)
