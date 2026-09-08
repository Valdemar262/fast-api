from abc import ABC

from app.models import Statement
from app.notification.base import BaseNotification


class StatementNotification(BaseNotification, ABC):
    def __init__(self, statement: Statement) -> None:
        self.statement = statement

    def _details(self) -> str:
        return (
            f"ID: {self.statement.id}\n"
            f"Title: {self.statement.title}\n"
            f"Number: {self.statement.number}\n"
            f"Date: {self.statement.date or '—'}"
        )


class StatementSubmittedNotification(StatementNotification):
    def subject(self) -> str:
        return "Statement submitted"

    def body(self) -> str:
        return f"Your statement has been submitted for review.\n\n{self._details()}"


class StatementApprovedNotification(StatementNotification):
    def subject(self) -> str:
        return "Statement approved"

    def body(self) -> str:
        return f"Your statement has been approved.\n\n{self._details()}"


class StatementRejectedNotification(StatementNotification):
    def subject(self) -> str:
        return "Statement rejected"

    def body(self) -> str:
        return f"Your statement has been rejected.\n\n{self._details()}"
