from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.enums import StatementStatus
from app.models.mixins import SoftDeleteMixin, TimestampMixin


class StatusHistory(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    statement_id: Mapped[int] = mapped_column(
        ForeignKey("statements.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
    )
    old_status: Mapped[StatementStatus]
    new_status: Mapped[StatementStatus]
