from collections.abc import Callable, Mapping

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import StatusTransitionType
from app.services.statement.strategies.approve import ApproveTransition
from app.services.statement.strategies.base import StatusTransitionStrategy
from app.services.statement.strategies.reject import RejectTransition
from app.services.statement.strategies.submit import SubmitTransition

_STRATEGIES: Mapping[StatusTransitionType, Callable[[AsyncSession], StatusTransitionStrategy]] = {
    StatusTransitionType.SUBMIT: SubmitTransition,
    StatusTransitionType.APPROVE: ApproveTransition,
    StatusTransitionType.REJECT: RejectTransition,
}


def resolve_strategy(
    transition: StatusTransitionType,
    session: AsyncSession,
) -> StatusTransitionStrategy:
    return _STRATEGIES[transition](session)
