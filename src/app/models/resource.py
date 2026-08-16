from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking


class Resource(TimestampMixin, Base):
    __tablename__ = "resources"

    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="resource",
        lazy="raise",
    )
