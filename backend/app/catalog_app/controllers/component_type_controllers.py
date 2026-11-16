from fastapi import APIRouter

from app.catalog_app import schemas as catalog_schemas
from app.catalog_app import services as catalog_services
from app.deps import CatalogListParams, DbSession


class ComponentTypeController:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/component-type", tags=["Component type"])
        self.router.add_api_route("/list", self.type_list, methods=["GET"], response_model=list[catalog_schemas.ComponentTypeRead])
        self.router.add_api_route("/create", self.type_create, methods=["POST"], status_code=201, response_model=catalog_schemas.ComponentTypeRead)
        self.router.add_api_route("/archive", self.type_archive, methods=["PATCH"], response_model=catalog_schemas.IdsResult)
        self.router.add_api_route("/unarchive", self.type_unarchive, methods=["PATCH"], response_model=catalog_schemas.IdsResult)
        self.router.add_api_route("/{type_id}", self.type_get, methods=["GET"], response_model=catalog_schemas.ComponentTypeRead)
        self.router.add_api_route("/{type_id}", self.type_update, methods=["PATCH"], response_model=catalog_schemas.ComponentTypeRead)

    async def type_list(self, db: DbSession, params: CatalogListParams):
        """Список типов. По умолчанию без архивных."""
        return await catalog_services.ComponentTypeService.get_list(db=db, params=params)

    async def type_create(self, db: DbSession, data: catalog_schemas.ComponentTypeCreate):
        """Подтип одного из трёх корней."""
        return await catalog_services.ComponentTypeService.create(db=db, data=data)

    async def type_get(self, db: DbSession, type_id: int):
        """Тип по id, в том числе архивный."""
        return await catalog_services.ComponentTypeService.get_by_id(db=db, type_id=type_id)

    async def type_update(self, db: DbSession, type_id: int, data: catalog_schemas.ComponentTypeUpdate):
        """Переименовать подтип. Имя системного корня фиксировано."""
        return await catalog_services.ComponentTypeService.update(db=db, type_id=type_id, data=data)

    async def type_archive(self, db: DbSession, data: catalog_schemas.IdsBody):
        """Архивировать типы. Корни и типы с живыми комплектующими пропускаются."""
        return await catalog_services.ComponentTypeService.archive(db=db, ids=data.ids)

    async def type_unarchive(self, db: DbSession, data: catalog_schemas.IdsBody):
        """Вернуть типы из архива."""
        return await catalog_services.ComponentTypeService.unarchive(db=db, ids=data.ids)
