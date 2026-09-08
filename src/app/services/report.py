from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import ReportPeriod, ReportType, StatementStatus
from app.reports import (
    BookingsByResourceCsvReport,
    CsvReport,
    StatementsSummaryCsvReport,
    StatementsTrendCsvReport,
    UserActivityCsvReport,
)
from app.repositories.report import ReportRepository
from app.schemas.report import (
    ResourceBookings,
    StatementsSummary,
    StatementsTrendPoint,
    UserActivity,
)


class ReportService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.reports = ReportRepository(session)

    async def build(self, report_type: ReportType, period: ReportPeriod) -> CsvReport:
        builders: dict[ReportType, Callable[[ReportPeriod], Awaitable[CsvReport]]] = {
            ReportType.STATEMENTS_SUMMARY: self._statements_summary,
            ReportType.BOOKINGS_BY_RESOURCE: self._bookings_by_resource,
            ReportType.USER_ACTIVITY: self._user_activity,
            ReportType.STATEMENTS_TREND: self._statements_trend,
        }
        return await builders[report_type](period)

    async def statements_summary(self, period: ReportPeriod) -> StatementsSummary:
        counts = await self.reports.statements_by_status(period.start_date())
        complete = {status: counts.get(status, 0) for status in StatementStatus}

        return StatementsSummary(period=period, counts=complete, total=sum(complete.values()))

    async def _statements_summary(self, period: ReportPeriod) -> CsvReport:
        return StatementsSummaryCsvReport(await self.statements_summary(period))

    async def bookings_by_resource(self, period: ReportPeriod) -> list[ResourceBookings]:
        rows = await self.reports.bookings_by_resource()
        return [
            ResourceBookings(resource_id=id_, resource_name=name, bookings_count=count)
            for id_, name, count in rows
        ]

    async def _bookings_by_resource(self, period: ReportPeriod) -> CsvReport:
        return BookingsByResourceCsvReport(await self.bookings_by_resource(period))

    async def user_activity(self, period: ReportPeriod) -> list[UserActivity]:
        rows = await self.reports.user_activity()
        return [
            UserActivity(
                user_id=id_,
                user_name=name,
                user_email=email,
                statements_count=statements,
                bookings_count=bookings,
            )
            for id_, name, email, statements, bookings in rows
        ]

    async def _user_activity(self, period: ReportPeriod) -> CsvReport:
        return UserActivityCsvReport(await self.user_activity(period))

    async def statements_trend(self, period: ReportPeriod) -> list[StatementsTrendPoint]:
        rows = await self.reports.statements_trend(period.start_date())
        return [StatementsTrendPoint(day=day, count=count) for day, count in rows]

    async def _statements_trend(self, period: ReportPeriod) -> CsvReport:
        return StatementsTrendCsvReport(await self.statements_trend(period))
