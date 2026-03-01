from routers import BaseRoute
from models import AuthLoginRequest, AuthLoginResponse
from fastapi import HTTPException

class AuthRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/auth",
            tags=["auth"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )
        
        self.router.post("/login", response_model=AuthLoginResponse)(self.login)
        self.router.post("/login/provider")(self.login_provider)
        self.router.post("/register")(self.register)
        self.router.post("/register/twofactor")(self.register_twofactor)
        self.router.post("/logout")(self.logout)
        self.router.post("/reset-password")(self.reset_password)
        self.router.post("/refresh-token")(self.refresh_token)
        self.router.post("/extension-token")(self.create_extension_token)
        self.router.post("/verify-extension-token")(self.verify_extension_token)
        self.router.post("/verify-twofactor")(self.verify_twofactor)

    async def login(self, request: AuthLoginRequest):
        try:
            return AuthLoginResponse(message="Login successful", data=request)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def register(self):
        pass

    async def register_twofactor(self):
        pass

    async def login_provider(self):
        pass

    async def logout(self):
        pass

    async def reset_password(self):
        pass

    async def create_extension_token(self):
        pass

    async def verify_extension_token(self):
        pass

    async def verify_twofactor(self):
        pass

    async def refresh_token(self):
        pass
