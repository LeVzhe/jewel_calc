from fastapi import APIRouter

from app.catalog_app import schemas as catalog_schemas
from app.catalog_app import services as catalog_services
from app.deps import DbSession, JewelryQuery


class JewelryController:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="/jewelry", tags=["Jewelry"])
        self.router.add_api_route(
            "/list",
            self.jewelry_list,
            methods=["GET"],
            response_model=catalog_schemas.JewelryList,
        )
        self.router.add_api_route(
            "/create",
            self.jewelry_create,
            methods=["POST"],
            status_code=201,
            response_model=catalog_schemas.JewelryRead,
        )
        self.router.add_api_route(
            "/archive",
            self.jewelry_archive,
            methods=["PATCH"],
            response_model=catalog_schemas.IdsResult,
        )
        self.router.add_api_route(
            "/unarchive",
            self.jewelry_unarchive,
            methods=["PATCH"],
            response_model=catalog_schemas.IdsResult,
        )
        self.router.add_api_route(
            "/{jewelry_id}",
            self.jewelry_get,
            methods=["GET"],
            response_model=catalog_schemas.JewelryRead,
        )
        self.router.add_api_route(
            "/{jewelry_id}",
            self.jewelry_update,
            methods=["PATCH"],
            response_model=catalog_schemas.JewelryRead,
        )

    async def jewelry_list(self, db: DbSession, params: JewelryQuery):
        """Список изделий. По умолчанию без архивных. Сначала недавно изменённые."""
        return await catalog_services.JewelryService.get_list(db=db, params=params)

    async def jewelry_create(self, db: DbSession, data: catalog_schemas.JewelryCreate):
        """Собрать изделие из комплектующих и загрузить фото в R2."""
        return await catalog_services.JewelryService.create(db=db, data=data)

    async def jewelry_get(self, db: DbSession, jewelry_id: int):
        """Изделие по id, в том числе архивное."""
        return await catalog_services.JewelryService.get_by_id(db=db, jewelry_id=jewelry_id)

    async def jewelry_update(self, db: DbSession, jewelry_id: int, data: catalog_schemas.JewelryUpdate):
        """Имя, состав или галерея. Уже стоящая деталь сохраняет свою первичную цену."""
        return await catalog_services.JewelryService.update(db=db, jewelry_id=jewelry_id, data=data)

    async def jewelry_archive(self, db: DbSession, data: catalog_schemas.IdsBody):
        """Архивировать изделия. Файлы в R2 остаются."""
        return await catalog_services.JewelryService.archive(db=db, ids=data.ids)

    async def jewelry_unarchive(self, db: DbSession, data: catalog_schemas.IdsBody):
        """Вернуть изделия из архива."""
        return await catalog_services.JewelryService.unarchive(db=db, ids=data.ids)
