from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

Money = Annotated[int, Field(strict=True, ge=0, le=99999999999999)]
Quantity = Annotated[int, Field(strict=True, ge=1, le=999)]
Name = Annotated[str, Field(min_length=1, max_length=120)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Output(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int


class Response[T](BaseModel):
    data: T


class NonNullPatch(Input):
    @model_validator(mode="before")
    @classmethod
    def reject_explicit_null(cls, data):
        if isinstance(data, dict) and any(v is None for v in data.values()):
            raise ValueError("Omit unchanged fields; explicit null is not allowed")
        return data
