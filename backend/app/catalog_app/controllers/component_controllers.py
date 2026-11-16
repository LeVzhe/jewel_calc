from fastapi import APIRouter

from app.catalog_app import schemas as catalog_schemas
from app.catalog_app import services as catalog_services
from app.deps import ComponentQuery, DbSession


class ComponentController:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/component", tags=["Component"])
        self.router.add_api_route("/list", self.component_list, methods=["GET"], response_model=catalog_schemas.ComponentList)
        self.router.add_api_route("/create", self.component_create, methods=["POST"], status_code=201, response_model=catalog_schemas.ComponentRead)
        self.router.add_api_route("/archive", self.component_archive, methods=["PATCH"], response_model=catalog_schemas.IdsResult)
        self.router.add_api_route("/unarchive", self.component_unarchive, methods=["PATCH"], response_model=catalog_schemas.IdsResult)
        self.router.add_api_route("/{component_id}", self.component_get, methods=["GET"], response_model=catalog_schemas.ComponentRead)
        self.router.add_api_route("/{component_id}", self.component_update, methods=["PATCH"], response_model=catalog_schemas.ComponentRead)

    async def component_list(self, db: DbSession, params: ComponentQuery):
        """Список комплектующих. По умолчанию без архивных."""
        return await catalog_services.ComponentService.get_list(db=db, params=params)

    async def component_create(self, db: DbSession, data: catalog_schemas.ComponentCreate):
        """Создать комплектующее и загрузить фото в R2."""
        return await catalog_services.ComponentService.create(db=db, data=data)

    async def component_get(self, db: DbSession, component_id: int):
        """Комплектующее по id, в том числе архивное."""
        return await catalog_services.ComponentService.get_by_id(db=db, component_id=component_id)

    async def component_update(self, db: DbSession, component_id: int, data: catalog_schemas.ComponentUpdate):
        """Обновить поля. Новая картинка заменяет файл по тому же guid."""
        return await catalog_services.ComponentService.update(db=db, component_id=component_id, data=data)

    async def component_archive(self, db: DbSession, data: catalog_schemas.IdsBody):
        """Архивировать комплектующие. Файлы в R2 остаются."""
        return await catalog_services.ComponentService.archive(db=db, ids=data.ids)

    async def component_unarchive(self, db: DbSession, data: catalog_schemas.IdsBody):
        """Вернуть комплектующие из архива."""
        return await catalog_services.ComponentService.unarchive(db=db, ids=data.ids)
