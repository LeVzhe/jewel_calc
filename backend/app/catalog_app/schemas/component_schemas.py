import datetime
import math
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated

import pydantic
from pydantic import Field

from app.catalog_app.schemas.color_schemas import ColorRead
from app.catalog_app.schemas.common_schemas import ListParams
from app.catalog_app.schemas.component_type_schemas import ComponentTypeRead
from utils.constants import ComponentUnit
from utils.text import clean_spaces

ShopLabel = Annotated[str, Field(max_length=500)]


def _round_cost(value: float) -> float:
    if not math.isfinite(value) or value < 0:
        raise ValueError("cost must be a finite number >= 0")
    quantized = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(quantized)


def _clean_shops(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        label = clean_spaces(raw)
        if not label:
            continue
        if len(label) > 500:
            raise ValueError("shop label is longer than 500")
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(label)
    return result


def _clean_article(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = clean_spaces(value)
    if not cleaned:
        return None
    if len(cleaned) > 128:
        raise ValueError("article is longer than 128")
    return cleaned


def _clean_name(value: str) -> str:
    cleaned = clean_spaces(value)
    if not cleaned:
        raise ValueError("name is empty")
    return cleaned


class ComponentListParams(ListParams):
    type_id: int | None = Field(default=None, ge=1)
    color_id: int | None = Field(default=None, ge=1)
    search: str | None = Field(default=None, max_length=255)

    @pydantic.field_validator("search")
    @classmethod
    def normalize_search(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = clean_spaces(value)
        return cleaned or None


class ComponentRead(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    guid: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_archived: bool
    name: str
    cost: float
    unit: ComponentUnit
    article: str | None
    image: str = Field(description="Публичный URL полного фото")
    image_preview: str = Field(description="Публичный URL превью")
    image_on_s3: bool
    image_preview_on_s3: bool
    type_id: int
    color_id: int | None
    type: ComponentTypeRead
    color: ColorRead | None
    shops: list[str]

    @pydantic.model_validator(mode="before")
    @classmethod
    def from_row(cls, value: object) -> object:
        if isinstance(value, dict):
            return value
        shops = []
        for item in getattr(value, "shops", []):
            shops.append(item if isinstance(item, str) else item.label)
        component_type = getattr(value, "component_type", None)
        if component_type is None:
            component_type = getattr(value, "type", None)
        return {
            "id": value.id,
            "guid": value.guid,
            "created_at": value.created_at,
            "updated_at": value.updated_at,
            "is_archived": value.is_archived,
            "name": value.name,
            "cost": value.cost,
            "unit": value.unit,
            "article": value.article,
            "image": value.image,
            "image_preview": value.image_preview,
            "image_on_s3": value.image_on_s3,
            "image_preview_on_s3": value.image_preview_on_s3,
            "type_id": value.type_id,
            "color_id": value.color_id,
            "type": component_type,
            "color": value.color,
            "shops": shops,
        }


class ComponentCreate(pydantic.BaseModel):
    name: str = Field(min_length=1, max_length=255)
    cost: float = Field(ge=0)
    unit: ComponentUnit = ComponentUnit.PCS
    article: str | None = Field(default=None, max_length=128)
    type_id: int = Field(ge=1)
    color_id: int | None = Field(default=None, ge=1)
    shops: list[ShopLabel] = Field(default_factory=list, max_length=30)
    image_base64: str = Field(
        min_length=1,
        max_length=20_000_000,
        description="Картинка base64. Допустим префикс data:image/...;base64,",
    )

    @pydantic.field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return _clean_name(value)

    @pydantic.field_validator("cost")
    @classmethod
    def normalize_cost(cls, value: float) -> float:
        return _round_cost(value)

    @pydantic.field_validator("article")
    @classmethod
    def normalize_article(cls, value: str | None) -> str | None:
        return _clean_article(value)

    @pydantic.field_validator("shops")
    @classmethod
    def normalize_shops(cls, value: list[str]) -> list[str]:
        return _clean_shops(value)

    @pydantic.field_validator("image_base64")
    @classmethod
    def normalize_image(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("image_base64 is empty")
        return cleaned


class ComponentUpdate(pydantic.BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    cost: float | None = Field(default=None, ge=0)
    unit: ComponentUnit | None = None
    article: str | None = Field(default=None, max_length=128)
    type_id: int | None = Field(default=None, ge=1)
    color_id: int | None = Field(default=None, ge=1)
    shops: list[ShopLabel] | None = Field(default=None, max_length=30)
    image_base64: str | None = Field(default=None, max_length=20_000_000)

    @pydantic.field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _clean_name(value)

    @pydantic.field_validator("cost")
    @classmethod
    def normalize_cost(cls, value: float | None) -> float | None:
        if value is None:
            return None
        return _round_cost(value)

    @pydantic.field_validator("article")
    @classmethod
    def normalize_article(cls, value: str | None) -> str | None:
        return _clean_article(value)

    @pydantic.field_validator("shops")
    @classmethod
    def normalize_shops(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return _clean_shops(value)

    @pydantic.field_validator("image_base64")
    @classmethod
    def normalize_image(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("image_base64 is empty")
        return cleaned
