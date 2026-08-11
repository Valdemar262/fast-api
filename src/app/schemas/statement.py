import datetime

from pydantic import Field

from app.enums import StatementStatus
from app.schemas.base import BaseSchema
from app.schemas.resource import ResourceRead
from app.schemas.user import UserRead


class StatementCreate(BaseSchema):
    title: str = Field(min_length=5, max_length=255)
    number: int
    date: datetime.datetime | None = None
    resource_id: int | None = None


class StatementUpdate(BaseSchema):
    title: str | None = None
    number: int | None = None
    date: datetime.datetime | None = None


class StatementRead(BaseSchema):
    id: int
    title: str
    number: int
    user_id: int
    status: StatementStatus
    date: datetime.date | None = None
    resource_id: int | None = None
    approved_by_id: int | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class StatementDetailRead(StatementRead):
    user: UserRead
    resource: ResourceRead | None = None
