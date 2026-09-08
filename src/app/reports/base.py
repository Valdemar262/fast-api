import csv
import io
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import UTC, datetime


class CsvReport(ABC):
    @property
    @abstractmethod
    def prefix(self) -> str: ...

    @property
    @abstractmethod
    def headers(self) -> list[str]: ...

    @abstractmethod
    def rows(self) -> Iterator[list[object]]: ...

    def filename(self) -> str:
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        return f"{self.prefix}_{stamp}.csv"

    def render(self) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(self.headers)
        writer.writerows(self.rows())
        return buffer.getvalue()
