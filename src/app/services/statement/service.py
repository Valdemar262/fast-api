from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import StatementStatus, StatusTransitionType, UserRole
from app.exceptions import InvalidStatusTransitionError, NotFoundError, PermissionDeniedError
from app.models import Statement, User
from app.repositories.resource import ResourceRepository
from app.repositories.statement import StatementRepository
from app.schemas import Page, StatementCreate, StatementDetailRead, StatementRead, StatementUpdate
from app.services.statement.strategies import resolve_strategy


class StatementService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.statements = StatementRepository(session)
        self.resources = ResourceRepository(session)

    async def get(self, statement_id: int) -> Statement:
        statement = await self.statements.get_by_id(statement_id)
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

    async def transition(self, statement_id: int, transition: StatusTransitionType, actor: User) -> Statement:
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
        return statement

    async def update(self, statement_id: int, payload: StatementUpdate) -> Statement:
        statement = await self.get(statement_id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(statement, field, value)

        await self.session.commit()
        return statement


    async def delete(self, statement_id: int) -> None:
        statement = await self.get(statement_id)
        await self.statements.delete(statement)
        await self.session.commit()
