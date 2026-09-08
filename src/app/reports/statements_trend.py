from collections.abc import Iterator

from app.reports.base import CsvReport
from app.schemas.report import StatementsTrendPoint


class StatementsTrendCsvReport(CsvReport):
    def __init__(self, points: list[StatementsTrendPoint]) -> None:
        self.points = points

    @property
    def prefix(self) -> str:
        return "statements_trend"

    @property
    def headers(self) -> list[str]:
        return ["Day", "Count"]

    def rows(self) -> Iterator[list[object]]:
        for point in self.points:
            yield [point.day.isoformat(), point.count]
