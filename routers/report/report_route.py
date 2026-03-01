from routers import BaseRoute
from typing import Any

class ReportRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/report",
            tags=["report"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.get("", response_model=Any)
        self.router.post("", response_model=Any)

    async def create_report(self):
        pass

    async def get_report_data(self):
        pass
