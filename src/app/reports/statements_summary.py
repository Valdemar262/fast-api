from collections.abc import Iterator

from app.reports.base import CsvReport
from app.schemas.report import StatementsSummary


class StatementsSummaryCsvReport(CsvReport):
    def __init__(self, summary: StatementsSummary) -> None:
        self.summary = summary

    @property
    def prefix(self) -> str:
        return "statements_summary"

    @property
    def headers(self) -> list[str]:
        return ["Status", "Count"]

    def rows(self) -> Iterator[list[object]]:
        for status, count in self.summary.counts.items():
            yield [status.value, count]
        yield ["total", self.summary.total]
