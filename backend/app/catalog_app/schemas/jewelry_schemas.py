from __future__ import annotations

import datetime
import math
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated

import pydantic
from pydantic import Field

from app.catalog_app.schemas.common_schemas import ListParams
from utils.constants import ComponentUnit
from utils.text import clean_spaces

ImagePayload = Annotated[str, Field(min_length=1, max_length=20_000_000)]
_MONEY = Decimal("0.01")
_QUANTITY = Decimal("0.001")


def _line_money(quantity: float, unit_price: float) -> float:
    amount = Decimal(str(quantity)) * Decimal(str(unit_price))
    return float(amount.quantize(_MONEY, rounding=ROUND_HALF_UP))


def _round_sale(value: float) -> float:
    if not math.isfinite(value) or value < 0:
        raise ValueError("sale price must be a finite number >= 0")
    return float(Decimal(str(value)).quantize(_MONEY, rounding=ROUND_HALF_UP))


def _round_quantity(value: float) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError("quantity must be a finite number > 0")
    quantized = Decimal(str(value)).quantize(_QUANTITY, rounding=ROUND_HALF_UP)
    if quantized <= 0:
        raise ValueError("quantity must be greater than 0")
    if quantized > Decimal("1000000"):
        raise ValueError("quantity is too large")
    return float(quantized)


def _clean_photo(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("image_base64 is empty")
    return cleaned


class JewelryListParams(ListParams):
    search: str | None = Field(default=None, max_length=255)

    @pydantic.field_validator("search")
    @classmethod
    def normalize_search(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = clean_spaces(value)
        return cleaned or None


class JewelryComponentRead(pydantic.BaseModel):
    id: int
    name: str
    cost: float
    unit: ComponentUnit
    is_archived: bool
    image_preview: str
    type_id: int
    type_name: str
    color_id: int | None
    color_name: str | None


class JewelryPartRead(pydantic.BaseModel):
    id: int
    component_id: int
    quantity: float
    unit_cost: float = Field(description="Цена комплектующего на момент добавления в изделие")
    cost: float = Field(description="Строка по сегодняшней цене комплектующего")
    initial_cost: float = Field(description="Строка по цене на момент добавления")
    component: JewelryComponentRead


class JewelryPhotoRead(pydantic.BaseModel):
    id: int
    guid: uuid.UUID
    image: str
    image_preview: str
    image_on_s3: bool
    image_preview_on_s3: bool


class JewelryRead(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    guid: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_archived: bool
    name: str
    cost: float = Field(description="Текущая себестоимость по живым ценам комплектующих")
    initial_cost: float = Field(description="Себестоимость по ценам на момент добавления деталей")
    sale_price: float = Field(description="Конечная цена, зафиксированная при сохранении")
    photos: list[JewelryPhotoRead]
    parts: list[JewelryPartRead]

    @pydantic.model_validator(mode="before")
    @classmethod
    def from_row(cls, value: object) -> object:
        if isinstance(value, dict):
            return value
        if isinstance(value, cls):
            return value.model_dump()

        photos = [
            {
                "id": photo.id,
                "guid": photo.guid,
                "image": photo.image,
                "image_preview": photo.image_preview,
                "image_on_s3": photo.image_on_s3,
                "image_preview_on_s3": photo.image_preview_on_s3,
            }
            for photo in value.photos
        ]
        parts: list[dict] = []
        current_total = Decimal("0")
        initial_total = Decimal("0")
        for part in value.parts:
            component = part.component
            color = component.color
            line_cost = _line_money(part.quantity, component.cost)
            line_initial = _line_money(part.quantity, part.unit_cost)
            current_total += Decimal(str(line_cost))
            initial_total += Decimal(str(line_initial))
            parts.append(
                {
                    "id": part.id,
                    "component_id": part.component_id,
                    "quantity": part.quantity,
                    "unit_cost": part.unit_cost,
                    "cost": line_cost,
                    "initial_cost": line_initial,
                    "component": {
                        "id": component.id,
                        "name": component.name,
                        "cost": component.cost,
                        "unit": component.unit,
                        "is_archived": component.is_archived,
                        "image_preview": component.image_preview,
                        "type_id": component.type_id,
                        "type_name": component.component_type.name,
                        "color_id": component.color_id,
                        "color_name": None if color is None else color.name,
                    },
                }
            )
        return {
            "id": value.id,
            "guid": value.guid,
            "created_at": value.created_at,
            "updated_at": value.updated_at,
            "is_archived": value.is_archived,
            "name": value.name,
            "cost": float(current_total),
            "initial_cost": float(initial_total),
            "sale_price": value.sale_price,
            "photos": photos,
            "parts": parts,
        }


class JewelryPartInput(pydantic.BaseModel):
    component_id: int = Field(ge=1)
    quantity: float = Field(gt=0, le=1_000_000)

    @pydantic.field_validator("quantity")
    @classmethod
    def normalize_quantity(cls, value: float) -> float:
        return _round_quantity(value)


class JewelryPhotoInput(pydantic.BaseModel):
    id: int | None = Field(default=None, ge=1)
    image_base64: str | None = Field(default=None, max_length=20_000_000)

    @pydantic.field_validator("image_base64")
    @classmethod
    def normalize_image(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _clean_photo(value)

    @pydantic.model_validator(mode="after")
    def one_source(self) -> JewelryPhotoInput:
        has_id = self.id is not None
        has_file = self.image_base64 is not None
        if has_id == has_file:
            raise ValueError("photo needs id or image_base64")
        return self


class JewelryCreate(pydantic.BaseModel):
    name: str = Field(min_length=1, max_length=255)
    parts: list[JewelryPartInput] = Field(min_length=1, max_length=100)
    photos: list[ImagePayload] = Field(min_length=1, max_length=8)
    sale_price: float = Field(ge=0)

    @pydantic.field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        cleaned = clean_spaces(value)
        if not cleaned:
            raise ValueError("name is empty")
        return cleaned

    @pydantic.field_validator("photos")
    @classmethod
    def normalize_photos(cls, value: list[str]) -> list[str]:
        return [_clean_photo(item) for item in value]

    @pydantic.field_validator("sale_price")
    @classmethod
    def normalize_sale(cls, value: float) -> float:
        return _round_sale(value)


class JewelryUpdate(pydantic.BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    parts: list[JewelryPartInput] | None = Field(default=None, min_length=1, max_length=100)
    photos: list[JewelryPhotoInput] | None = Field(default=None, min_length=1, max_length=8)
    sale_price: float | None = Field(default=None, ge=0)

    @pydantic.field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = clean_spaces(value)
        if not cleaned:
            raise ValueError("name is empty")
        return cleaned

    @pydantic.field_validator("sale_price")
    @classmethod
    def normalize_sale(cls, value: float | None) -> float | None:
        if value is None:
            return None
        return _round_sale(value)


class JewelryList(pydantic.BaseModel):
    items: list[JewelryRead]
    total: int
