from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema


class ResourceBase(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    type: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    type: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class ResourceRead(ResourceBase):
    id: int
    created_at: datetime
    updated_at: datetime
