from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog_app.models import ComponentType
from app.catalog_app.schemas.common_schemas import IdSkip, IdsResult, ListParams
from app.catalog_app.schemas.component_type_schemas import ComponentTypeRead
from utils.constants import SkipReason
from utils.text import utcnow


class ComponentTypeRepository:
    @classmethod
    async def get_by_id(cls, db: AsyncSession, type_id: int) -> ComponentTypeRead | None:
        result = await db.execute(select(ComponentType).where(ComponentType.id == type_id))
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return ComponentTypeRead.model_validate(row)

    @classmethod
    async def get_list(cls, db: AsyncSession, params: ListParams) -> list[ComponentTypeRead]:
        stmt = select(ComponentType).order_by(
            ComponentType.parent_id.is_(None).desc(),
            ComponentType.name,
            ComponentType.id,
        )
        if not params.include_archived:
            stmt = stmt.where(ComponentType.is_archived.is_(False))
        stmt = stmt.offset(params.skip).limit(params.limit)
        result = await db.execute(stmt)
        return [ComponentTypeRead.model_validate(row) for row in result.scalars().all()]

    @classmethod
    async def create(cls, db: AsyncSession, name: str, parent_id: int) -> ComponentTypeRead:
        row = ComponentType(name=name, name_key=name.casefold(), parent_id=parent_id, is_system=False)
        db.add(row)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise
        return ComponentTypeRead.model_validate(row)

    @classmethod
    async def update_name(cls, db: AsyncSession, type_id: int, name: str) -> ComponentTypeRead | None:
        result = await db.execute(select(ComponentType).where(ComponentType.id == type_id))
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
        return ComponentTypeRead.model_validate(row)

    @classmethod
    async def set_archived(cls, db: AsyncSession, ids: list[int], *, archived: bool) -> IdsResult:
        unique_ids = list(dict.fromkeys(ids))
        result = await db.execute(select(ComponentType).where(ComponentType.id.in_(unique_ids)))
        rows = {row.id: row for row in result.scalars().all()}
        changed: list[int] = []
        skipped: list[IdSkip] = []
        for item_id in unique_ids:
            row = rows.get(item_id)
            if row is None:
                skipped.append(IdSkip(id=item_id, reason=SkipReason.NOT_FOUND))
                continue
            if archived:
                if row.is_system:
                    skipped.append(IdSkip(id=item_id, reason=SkipReason.SYSTEM_TYPE))
                    continue
                if row.is_archived:
                    skipped.append(IdSkip(id=item_id, reason=SkipReason.ALREADY_ARCHIVED))
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
