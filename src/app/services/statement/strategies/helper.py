from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import StatementStatus
from app.models import Statement, StatusHistory


def apply_status(
        session: AsyncSession,
        statement: Statement,
        new_status: StatementStatus,
) -> None:
    session.add(
        StatusHistory(
            statement_id=statement.id,
            old_status=statement.status,
            new_status=new_status,
        )
    )

    statement.status = new_status
