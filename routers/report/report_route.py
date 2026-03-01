from routers import BaseRoute
from models.report_model import ReportModelResponse, ReportModelRequest

class ReportRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/report",
            tags=["report"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.get("", response_model=ReportModelResponse)(self.get_report_data)
        self.router.post("", response_model=ReportModelRequest)(self.create_report)

    async def create_report(self):
        pass

    async def get_report_data(self):
        return ReportModelResponse(
            message="Report generated successfully",
            data=[]
        )
