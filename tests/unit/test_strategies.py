from collections.abc import Awaitable, Callable

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import StatementStatus, StatusTransitionType
from app.exceptions import InvalidStatusTransitionError
from app.models import Resource, Statement, StatusHistory, User
from app.services.statement.strategies import resolve_strategy
from app.services.statement.strategies.approve import ApproveTransition
from app.services.statement.strategies.reject import RejectTransition
from app.services.statement.strategies.submit import SubmitTransition

MakeStatement = Callable[..., Awaitable[Statement]]
MakeResource = Callable[..., Awaitable[Resource]]

TRANSITION_MATRIX = [
    (StatementStatus.DRAFT, StatusTransitionType.SUBMIT, True),
    (StatementStatus.DRAFT, StatusTransitionType.APPROVE, False),
    (StatementStatus.DRAFT, StatusTransitionType.REJECT, False),
    (StatementStatus.SUBMITTED, StatusTransitionType.SUBMIT, False),
    (StatementStatus.SUBMITTED, StatusTransitionType.APPROVE, True),
    (StatementStatus.SUBMITTED, StatusTransitionType.REJECT, True),
    (StatementStatus.APPROVED, StatusTransitionType.SUBMIT, False),
    (StatementStatus.APPROVED, StatusTransitionType.APPROVE, False),
    (StatementStatus.APPROVED, StatusTransitionType.REJECT, False),
    (StatementStatus.REJECTED, StatusTransitionType.SUBMIT, False),
    (StatementStatus.REJECTED, StatusTransitionType.APPROVE, False),
    (StatementStatus.REJECTED, StatusTransitionType.REJECT, False),
]


@pytest.mark.parametrize(
    ("status", "transition", "expected"),
    TRANSITION_MATRIX,
    ids=[f"{status.value}-{transition.value}" for status, transition, _ in TRANSITION_MATRIX],
)
async def test_transition_matrix(
    session: AsyncSession,
    client_user: User,
    admin_user: User,
    make_statement: MakeStatement,
    status: StatementStatus,
    transition: StatusTransitionType,
    expected: bool,
) -> None:
    statement = await make_statement(client_user, status=status)
    actor = client_user if transition == StatusTransitionType.SUBMIT else admin_user
    strategy = resolve_strategy(transition, session)

    assert strategy.can_transition(statement, actor) is expected


async def test_submit_refused_for_non_owner(
    session: AsyncSession,
    client_user: User,
    admin_user: User,
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(client_user, status=StatementStatus.DRAFT)

    assert SubmitTransition(session).can_transition(statement, admin_user) is False


async def test_approve_allowed_for_admin_who_is_not_the_owner(
    session: AsyncSession,
    client_user: User,
    admin_user: User,
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(client_user, status=StatementStatus.SUBMITTED)

    assert ApproveTransition(session).can_transition(statement, admin_user) is True


async def test_submit_sets_status_and_writes_history(
    session: AsyncSession,
    client_user: User,
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(client_user, status=StatementStatus.DRAFT)

    SubmitTransition(session).execute(statement, client_user)
    await session.flush()

    assert statement.status == StatementStatus.SUBMITTED

    history = (await session.scalars(select(StatusHistory))).all()
    assert len(history) == 1
    assert history[0].statement_id == statement.id
    assert history[0].old_status == StatementStatus.DRAFT
    assert history[0].new_status == StatementStatus.SUBMITTED


async def test_approve_sets_approved_by_and_writes_history(
    session: AsyncSession,
    client_user: User,
    admin_user: User,
    make_statement: MakeStatement,
    make_resource: MakeResource,
) -> None:
    resource = await make_resource()
    statement = await make_statement(
        client_user, status=StatementStatus.SUBMITTED, resource_id=resource.id
    )

    ApproveTransition(session).execute(statement, admin_user)
    await session.flush()

    assert statement.status == StatementStatus.APPROVED
    assert statement.approved_by_id == admin_user.id

    history = (await session.scalars(select(StatusHistory))).all()
    assert len(history) == 1
    assert history[0].old_status == StatementStatus.SUBMITTED
    assert history[0].new_status == StatementStatus.APPROVED


async def test_approve_without_resource_is_refused(
    session: AsyncSession,
    client_user: User,
    admin_user: User,
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(
        client_user, status=StatementStatus.SUBMITTED, resource_id=None
    )

    with pytest.raises(InvalidStatusTransitionError):
        ApproveTransition(session).execute(statement, admin_user)


async def test_reject_sets_status_and_writes_history(
    session: AsyncSession,
    client_user: User,
    admin_user: User,
    make_statement: MakeStatement,
) -> None:
    statement = await make_statement(client_user, status=StatementStatus.SUBMITTED)

    RejectTransition(session).execute(statement, admin_user)
    await session.flush()

    assert statement.status == StatementStatus.REJECTED
    assert statement.approved_by_id is None

    history = (await session.scalars(select(StatusHistory))).all()
    assert len(history) == 1
    assert history[0].old_status == StatementStatus.SUBMITTED
    assert history[0].new_status == StatementStatus.REJECTED


@pytest.mark.parametrize(
    ("transition", "expected_type"),
    [
        (StatusTransitionType.SUBMIT, SubmitTransition),
        (StatusTransitionType.APPROVE, ApproveTransition),
        (StatusTransitionType.REJECT, RejectTransition),
    ],
    ids=[t.value for t in StatusTransitionType],
)
def test_resolver_returns_the_right_strategy(
    session: AsyncSession,
    transition: StatusTransitionType,
    expected_type: type,
) -> None:
    assert isinstance(resolve_strategy(transition, session), expected_type)
