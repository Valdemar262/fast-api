from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import StatementStatus
from app.models import Statement, User
from app.services.statement.strategies import StatusTransitionStrategy
from app.services.statement.strategies.helper import apply_status


class RejectTransition(StatusTransitionStrategy):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def can_transition(self, statement: Statement, actor: User) -> bool:
        return statement.status == StatementStatus.SUBMITTED

    def execute(self, statement: Statement, actor: User) -> None:
        apply_status(self.session, statement, StatementStatus.REJECTED)
