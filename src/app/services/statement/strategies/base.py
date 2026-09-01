from typing import Protocol

from app.models import Statement, User


class StatusTransitionStrategy(Protocol):
    def can_transition(self, statement: Statement, actor: User) -> bool: ...

    def execute(self, statement: Statement, actor: User) -> None: ...
