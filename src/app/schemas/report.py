import datetime

from app.enums import ReportPeriod, StatementStatus
from app.schemas.base import BaseSchema


class StatementsSummary(BaseSchema):
    period: ReportPeriod
    counts: dict[StatementStatus, int]
    total: int


class ResourceBookings(BaseSchema):
    resource_id: int
    resource_name: str
    bookings_count: int


class UserActivity(BaseSchema):
    user_id: int
    user_name: str
    user_email: str
    statements_count: int
    bookings_count: int


class StatementsTrendPoint(BaseSchema):
    day: datetime.date
    count: int
