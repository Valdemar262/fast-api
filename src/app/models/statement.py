import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.enums import StatementStatus
from app.models.mixins import SoftDeleteMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.resource import Resource
    from app.models.user import User


class Statement(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "statements"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    number: Mapped[int]
    date: Mapped[datetime.date | None] = mapped_column(Date)
    status: Mapped[StatementStatus] = mapped_column(
        default=StatementStatus.DRAFT,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        index=True,
    )
    approved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    user: Mapped["User"] = relationship(
        foreign_keys=[user_id],
        back_populates="statements",
        lazy="raise",
    )

    approved_by: Mapped["User | None"] = relationship(
        foreign_keys=[approved_by_id],
        lazy="raise",
    )

    resource: Mapped["Resource | None"] = relationship(lazy="raise")
