from pydantic import Field, BaseModel
from models import BaseResponseModel

class UserStatItem(BaseModel):
  total_users: int = Field(description="Total number of users")
  active_users: int = Field(description="Active users in last 30 days")
  new_users_today: int = Field(description="New users registered today")
  new_users_this_week: int = Field(description="New users this week")
  new_users_this_month: int = Field(description="New users this month")

class UserStatResponse(BaseResponseModel):
  data: UserStatItem

class UserActivityItem(BaseModel):
  date: str = Field(description="Date", examples=["2025-01-15"])
  active_users: int = Field(description="Active users on this date")
  new_users: int = Field(description="New users registered")
  total_actions: int = Field(description="Total user actions")

class UserActivityResponse(BaseResponseModel):
  data: list[UserActivityItem]

class UserRoleStatItem(BaseModel):
  role: str = Field(description="User role: admin, user, moderator")
  count: int = Field(description="Number of users with this role")
  percentage: float = Field(description="Percentage of total users")

class UserRoleStatResponse(BaseResponseModel):
  data: list[UserRoleStatItem]

class TopUserItem(BaseModel):
  user_id: str = Field(description="User ID")
  username: str = Field(description="Username")
  email: str = Field(description="User email")
  prediction_count: int = Field(description="Number of predictions made")
  report_count: int = Field(description="Number of reports submitted")
  last_active: str = Field(description="Last activity timestamp")

class TopUserResponse(BaseResponseModel):
  data: list[TopUserItem]
