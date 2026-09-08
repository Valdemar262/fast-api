from collections.abc import Iterator

from app.reports.base import CsvReport
from app.schemas.report import UserActivity


class UserActivityCsvReport(CsvReport):
    def __init__(self, rows: list[UserActivity]) -> None:
        self._rows = rows

    @property
    def prefix(self) -> str:
        return "user_activity"

    @property
    def headers(self) -> list[str]:
        return ["User ID", "User name", "User email", "Statements count", "Bookings count"]

    def rows(self) -> Iterator[list[object]]:
        for row in self._rows:
            yield [
                row.user_id,
                row.user_name,
                row.user_email,
                row.statements_count,
                row.bookings_count,
            ]
