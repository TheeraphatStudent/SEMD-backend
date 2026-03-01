from models import UserStatResponse, UserActivityResponse, UserRoleStatResponse, TopUserResponse
from routers import BaseRoute

class UserStatRoute(BaseRoute):
  def __init__(self):
        super().__init__(
            prefix="/stat/user",
            tags=["stat-user"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.get('', response_model=UserStatResponse)(self.get_user_stat)
        self.router.get('/activity', response_model=UserActivityResponse)(self.get_user_activity)
        self.router.get('/role', response_model=UserRoleStatResponse)(self.get_user_role)
        self.router.get('/top', response_model=TopUserResponse)(self.get_top_users)

  async def get_user_stat(self):
      pass
  
  async def get_user_activity(self):
      pass
  
  async def get_user_role(self):
      pass
  
  async def get_top_users(self):
      pass
