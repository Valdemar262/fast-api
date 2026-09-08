from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import StatementStatus, StatusTransitionType, UserRole
from app.exceptions import InvalidStatusTransitionError, NotFoundError, PermissionDeniedError
from app.models import Statement, User
from app.notification.statement import (
    StatementApprovedNotification,
    StatementNotification,
    StatementRejectedNotification,
    StatementSubmittedNotification,
)
from app.repositories.resource import ResourceRepository
from app.repositories.statement import StatementRepository
from app.repositories.user import UserRepository
from app.schemas import Page, StatementCreate, StatementDetailRead, StatementRead, StatementUpdate
from app.services.statement.strategies import resolve_strategy


class StatementService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.statements = StatementRepository(session)
        self.resources = ResourceRepository(session)
        self.users = UserRepository(session)

    async def get(self, statement_id: int) -> Statement:
        statement = await self.statements.get_active(statement_id)
        if statement is None:
            raise NotFoundError(f"Statement for ID: {statement_id} not found")
        return statement

    async def create(self, *, payload: StatementCreate, user_id: int) -> Statement:
        if payload.resource_id is not None:
            resource = await self.resources.get_by_id(payload.resource_id)
            if resource is None:
                raise NotFoundError(f"Resource {payload.resource_id} not found")

        statement = await self.statements.create(
            **payload.model_dump(),
            status=StatementStatus.DRAFT,
            user_id=user_id,
        )
        await self.session.commit()
        return statement

    async def list_statements(self, user: User, limit: int, offset: int) -> Page[StatementRead]:
        owner_id = user.id if user.role == UserRole.CLIENT else None
        items = await self.statements.list_for_user(
            owner_id,
            limit=limit,
            offset=offset,
        )
        total = await self.statements.count_for_user(owner_id)

        return Page(
            items=[StatementRead.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_statement_by_id(self, statement_id: int, actor: User) -> StatementDetailRead:
        statement = await self.statements.get_with_relations(statement_id)
        if statement is None:
            raise NotFoundError(f"Statement {statement_id} not found")
        if statement.user_id != actor.id and actor.role != UserRole.ADMIN:
            raise PermissionDeniedError("You can only view your own statements")
        return StatementDetailRead.model_validate(statement)

    async def transition(
        self, statement_id: int, transition: StatusTransitionType, actor: User
    ) -> Statement:
        statement = await self.statements.get_active(statement_id)
        if statement is None:
            raise NotFoundError(f"Statement {statement_id} not found")

        strategy = resolve_strategy(transition, self.session)

        if not strategy.can_transition(statement, actor):
            raise InvalidStatusTransitionError(
                f"Cannot {transition.value} a statement in status {statement.status.value}"
            )

        strategy.execute(statement, actor)
        await self.session.commit()

        await self._notify_transition(statement, transition)  # ← потом уведомляем
        return statement

    async def update(self, statement_id: int, payload: StatementUpdate, actor: User) -> Statement:
        statement = await self.get(statement_id)

        if statement.user_id != actor.id and actor.role != UserRole.ADMIN:
            raise PermissionDeniedError("You can only update your own statements")

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(statement, field, value)

        await self.session.commit()
        return statement

    async def delete(self, statement_id: int, actor: User) -> None:
        statement = await self.get(statement_id)
        if statement.user_id != actor.id and actor.role != UserRole.ADMIN:
            raise PermissionDeniedError("You can only delete your own statements")
        statement.deleted_at = datetime.now(UTC)
        await self.session.commit()

    _NOTIFICATIONS: ClassVar[dict[StatusTransitionType, type[StatementNotification]]] = {
        StatusTransitionType.SUBMIT: StatementSubmittedNotification,
        StatusTransitionType.APPROVE: StatementApprovedNotification,
        StatusTransitionType.REJECT: StatementRejectedNotification,
    }

    async def _notify_transition(
        self, statement: Statement, transition: StatusTransitionType
    ) -> None:
        owner = await self.users.get_by_id(statement.user_id)
        if owner is None:
            return

        self._NOTIFICATIONS[transition](statement).send(owner.email)
