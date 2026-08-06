from enum import Enum as PyEnum
from typing import Any, Callable

from sqlalchemy import Enum as SAEnum, MetaData

from app.enums import StatementStatus, UserRole

from sqlalchemy.orm import DeclarativeBase


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

def _enum_values(enum_cls: type[PyEnum]) -> list[Callable[[], Any]]:
    return [member.value for member in enum_cls]


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    type_annotation_map = {
        UserRole: SAEnum(UserRole, name="userrole", values_callable=_enum_values),
        StatementStatus: SAEnum(
            StatementStatus, name="statementstatus", values_callable=_enum_values
        ),
    }
