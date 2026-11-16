from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog_app.models import Color, Component
from app.catalog_app.schemas.color_schemas import ColorRead
from app.catalog_app.schemas.common_schemas import IdSkip, IdsResult, ListParams
from utils.constants import SkipReason
from utils.text import utcnow


class ColorRepository:
    @classmethod
    async def get_by_id(cls, db: AsyncSession, color_id: int) -> ColorRead | None:
        result = await db.execute(select(Color).where(Color.id == color_id))
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return ColorRead.model_validate(row)

    @classmethod
    async def get_list(cls, db: AsyncSession, params: ListParams) -> list[ColorRead]:
        stmt = select(Color).order_by(Color.name, Color.id)
        if not params.include_archived:
            stmt = stmt.where(Color.is_archived.is_(False))
        stmt = stmt.offset(params.skip).limit(params.limit)
        result = await db.execute(stmt)
        return [ColorRead.model_validate(row) for row in result.scalars().all()]

    @classmethod
    async def create(cls, db: AsyncSession, name: str) -> ColorRead:
        row = Color(name=name, name_key=name.casefold())
        db.add(row)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise
        return ColorRead.model_validate(row)

    @classmethod
    async def update_name(cls, db: AsyncSession, color_id: int, name: str) -> ColorRead | None:
        result = await db.execute(select(Color).where(Color.id == color_id))
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.name = name
        row.name_key = name.casefold()
        row.updated_at = utcnow()
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise
        return ColorRead.model_validate(row)

    @classmethod
    async def set_archived(cls, db: AsyncSession, ids: list[int], *, archived: bool) -> IdsResult:
        unique_ids = list(dict.fromkeys(ids))
        result = await db.execute(select(Color).where(Color.id.in_(unique_ids)))
        rows = {row.id: row for row in result.scalars().all()}
        used_ids: set[int] = set()
        if archived and unique_ids:
            count_result = await db.execute(
                select(Component.color_id)
                .where(
                    Component.color_id.in_(unique_ids),
                    Component.is_archived.is_(False),
                )
                .distinct()
            )
            used_ids = {item for item in count_result.scalars().all() if item is not None}

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
                if row.id in used_ids:
                    skipped.append(IdSkip(id=item_id, reason=SkipReason.USED_BY_COMPONENTS))
                    continue
                row.is_archived = True
            else:
                if not row.is_archived:
                    skipped.append(IdSkip(id=item_id, reason=SkipReason.ALREADY_ACTIVE))
                    continue
                row.is_archived = False
            row.updated_at = utcnow()
            changed.append(row.id)

        if changed:
            await db.commit()
        return IdsResult(ids=changed, skipped=skipped)
