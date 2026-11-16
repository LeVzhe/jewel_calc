import datetime
import uuid

import pydantic
from pydantic import Field

from utils.text import clean_spaces


class ComponentTypeRead(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    guid: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_archived: bool
    name: str
    parent_id: int | None
    is_system: bool


class ComponentTypeCreate(pydantic.BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Название подтипа")
    parent_id: int = Field(ge=1, description="Id корня: фурнитура, упаковка или нить")

    @pydantic.field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        cleaned = clean_spaces(value)
        if not cleaned:
            raise ValueError("name is empty")
        return cleaned


class ComponentTypeUpdate(pydantic.BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)

    @pydantic.field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = clean_spaces(value)
        if not cleaned:
            raise ValueError("name is empty")
        return cleaned
