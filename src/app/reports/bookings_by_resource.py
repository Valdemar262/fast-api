from collections.abc import Iterator

from app.reports.base import CsvReport
from app.schemas.report import ResourceBookings


class BookingsByResourceCsvReport(CsvReport):
    def __init__(self, rows: list[ResourceBookings]) -> None:
        self._rows = rows

    @property
    def prefix(self) -> str:
        return "bookings_by_resource"

    @property
    def headers(self) -> list[str]:
        return ["Resource ID", "Resource name", "Bookings count"]

    def rows(self) -> Iterator[list[object]]:
        for row in self._rows:
            yield [row.resource_id, row.resource_name, row.bookings_count]
