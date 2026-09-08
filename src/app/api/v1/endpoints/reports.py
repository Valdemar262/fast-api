from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.deps import ReportServiceDep, require_role
from app.enums import ReportPeriod, ReportType, UserRole

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/{report_type}",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
    response_class=StreamingResponse,
    summary="Download a report as CSV",
    responses={
        200: {"content": {"text/csv": {}}, "description": "CSV file"},
        401: {"description": "Missing or invalid token"},
        403: {"description": "Requires the admin role"},
    },
)
async def download_report(
    report_type: ReportType,
    service: ReportServiceDep,
    period: Annotated[ReportPeriod, Query()] = ReportPeriod.MONTH,
) -> StreamingResponse:
    report = await service.build(report_type, period)

    return StreamingResponse(
        iter([report.render()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{report.filename()}"'},
    )
