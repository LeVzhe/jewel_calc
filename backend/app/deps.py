from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog_app.schemas.common_schemas import ListParams
from app.catalog_app.schemas.component_schemas import ComponentListParams
from app.catalog_app.schemas.jewelry_schemas import JewelryListParams
from utils.db_utils import DbManager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with DbManager.session_factory() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]
CatalogListParams = Annotated[ListParams, Depends()]
ComponentQuery = Annotated[ComponentListParams, Depends()]
JewelryQuery = Annotated[JewelryListParams, Depends()]
