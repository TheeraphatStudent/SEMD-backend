from routers import BaseRoute
from models import MLServiceResponse

class MLRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/ml",
            tags=["ml"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.get("/service", response_model=MLServiceResponse)(self.get_service)


    def get_service(self):
        return None
