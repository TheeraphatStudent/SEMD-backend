from fastapi import APIRouter


class BaseRoute:
    def __init__(self, prefix: str, tags: list, responses: dict):
        self.prefix = prefix
        self.tags = tags
        self.responses = responses

        self.router = APIRouter(
            prefix=self.prefix,
            tags=self.tags,
            responses=self.responses
        )

    def get_router(self):
        return self.router
