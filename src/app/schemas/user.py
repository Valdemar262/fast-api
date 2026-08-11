from datetime import date, datetime

from pydantic import EmailStr, Field

from app.enums import UserRole
from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    address: str | None = None
    birthday: date | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)


class UserUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    address: str | None = None
    birthday: date | None = None


class UserRead(UserBase):
    id: int
    role: UserRole
    created_at: datetime
    updated_at: datetime
