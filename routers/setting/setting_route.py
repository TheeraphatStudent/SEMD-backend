from routers import BaseRoute


class SettingRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/setting",
            tags=["Setting"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

    def setQueueJob(self):
        pass
