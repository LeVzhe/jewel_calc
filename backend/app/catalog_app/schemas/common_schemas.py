from typing import Annotated

import pydantic
from pydantic import Field


class ListParams(pydantic.BaseModel):
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=200)
    include_archived: bool = False


class IdSkip(pydantic.BaseModel):
    id: int
    reason: str


class IdsResult(pydantic.BaseModel):
    ids: list[int]
    skipped: list[IdSkip]


class IdsBody(pydantic.BaseModel):
    ids: list[Annotated[int, Field(ge=1)]] = Field(min_length=1, max_length=500)
