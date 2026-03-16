from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from libs.types.enums import RoleType


class UserUpdateRequest(BaseModel):
    username: Optional[str] = Field(
        None, min_length=3, max_length=32, description='Username')
    email: Optional[EmailStr] = Field(None, description='Email address')
    full_name: Optional[str] = Field(
        None, min_length=1, max_length=512, description='Full name')
    birthday: Optional[datetime] = Field(None, description='Birthday')
    profile_img_uri: Optional[str] = Field(
        None, description='Profile image URI')


class PasswordResetRequest(BaseModel):
    current_password: str = Field(..., min_length=8,
                                  description='Current password')
    new_password: str = Field(..., min_length=8, description='New password')
    confirm_password: str = Field(..., min_length=8,
                                  description='Confirm new password')

    def validate_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError('New password and confirm password do not match')
        return self


class AdminCreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32,
                          description='Username')
    email: EmailStr = Field(..., description='Email address')
    full_name: str = Field(..., min_length=1,
                           max_length=512, description='Full name')
    password: str = Field(..., min_length=8, description='Password')
    role: RoleType = Field(RoleType.MEMBER, description='User role')
    birthday: Optional[datetime] = Field(None, description='Birthday')
    profile_img_uri: Optional[str] = Field(
        None, description='Profile image URI')


class AdminUpdateUserRequest(BaseModel):
    username: Optional[str] = Field(
        None, min_length=3, max_length=32, description='Username')
    email: Optional[EmailStr] = Field(None, description='Email address')
    full_name: Optional[str] = Field(
        None, min_length=1, max_length=512, description='Full name')
    birthday: Optional[datetime] = Field(None, description='Birthday')
    profile_img_uri: Optional[str] = Field(
        None, description='Profile image URI')
    role: Optional[RoleType] = Field(
        None, description='User role (Master Admin only)')


class AdminPasswordResetRequest(BaseModel):
    new_password: str = Field(..., min_length=8, description='New password')
    confirm_password: str = Field(..., min_length=8,
                                  description='Confirm new password')

    def validate_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError('New password and confirm password do not match')
        return self
