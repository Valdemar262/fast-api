from datetime import UTC, datetime, timedelta
from enum import StrEnum


class UserRole(StrEnum):
    CLIENT = "client"
    ADMIN = "admin"


class StatementStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class StatusTransitionType(StrEnum):
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"


class ReportPeriod(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"

    def start_date(self) -> datetime | None:
        now = datetime.now(UTC)
        match self:
            case ReportPeriod.DAY:
                return now - timedelta(days=1)
            case ReportPeriod.WEEK:
                return now - timedelta(weeks=1)
            case ReportPeriod.MONTH:
                return now - timedelta(days=30)
            case ReportPeriod.YEAR:
                return now - timedelta(days=365)
            case ReportPeriod.ALL:
                return None


class ReportType(StrEnum):
    STATEMENTS_SUMMARY = "statements_summary"
    BOOKINGS_BY_RESOURCE = "bookings_by_resource"
    USER_ACTIVITY = "user_activity"
    STATEMENTS_TREND = "statements_trend"
