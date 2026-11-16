from fastapi import APIRouter

from app.catalog_app import schemas as catalog_schemas
from app.catalog_app import services as catalog_services
from app.deps import CatalogListParams, DbSession


class ColorController:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/color", tags=["Color"])
        self.router.add_api_route("/list", self.color_list, methods=["GET"], response_model=list[catalog_schemas.ColorRead])
        self.router.add_api_route("/create", self.color_create, methods=["POST"], status_code=201, response_model=catalog_schemas.ColorRead)
        self.router.add_api_route("/archive", self.color_archive, methods=["PATCH"], response_model=catalog_schemas.IdsResult)
        self.router.add_api_route("/unarchive", self.color_unarchive, methods=["PATCH"], response_model=catalog_schemas.IdsResult)
        self.router.add_api_route("/{color_id}", self.color_get, methods=["GET"], response_model=catalog_schemas.ColorRead)
        self.router.add_api_route("/{color_id}", self.color_update, methods=["PATCH"], response_model=catalog_schemas.ColorRead)

    async def color_list(self, db: DbSession, params: CatalogListParams):
        """Список цветов. По умолчанию без архивных."""
        return await catalog_services.ColorService.get_list(db=db, params=params)

    async def color_create(self, db: DbSession, data: catalog_schemas.ColorCreate):
        """Новый цвет в справочнике."""
        return await catalog_services.ColorService.create(db=db, data=data)

    async def color_get(self, db: DbSession, color_id: int):
        """Цвет по id, в том числе архивный."""
        return await catalog_services.ColorService.get_by_id(db=db, color_id=color_id)

    async def color_update(self, db: DbSession, color_id: int, data: catalog_schemas.ColorUpdate):
        """Переименовать цвет."""
        return await catalog_services.ColorService.update(db=db, color_id=color_id, data=data)

    async def color_archive(self, db: DbSession, data: catalog_schemas.IdsBody):
        """Архивировать цвета. Цвет с живыми комплектующими пропускается."""
        return await catalog_services.ColorService.archive(db=db, ids=data.ids)

    async def color_unarchive(self, db: DbSession, data: catalog_schemas.IdsBody):
        """Вернуть цвета из архива."""
        return await catalog_services.ColorService.unarchive(db=db, ids=data.ids)
