from sqlalchemy.orm import Session
from typing import List

from database import User, UrlFlag
from models.url_flag_request import UrlFlagCreateRequest, UrlFlagUpdateRequest
from models.url_flag_model import UrlFlagModel
from services.url_flag_service import UrlFlagService


class UrlFlagControl:

    @classmethod
    def create_flag(cls, user: User, request: UrlFlagCreateRequest, db: Session) -> UrlFlagModel:
        flag = UrlFlagService.create_flag(user, request, db)
        return UrlFlagModel.model_validate(flag)

    @classmethod
    def update_flag(cls, user: User, flag_id: int, request: UrlFlagUpdateRequest, db: Session) -> UrlFlagModel:
        flag = UrlFlagService.update_flag(user, flag_id, request, db)
        return UrlFlagModel.model_validate(flag)

    @classmethod
    def delete_flag(cls, user: User, flag_id: int, db: Session) -> bool:
        return UrlFlagService.delete_flag(user, flag_id, db)

    @classmethod
    def get_flag(cls, flag_id: int, db: Session) -> UrlFlagModel:
        flag = UrlFlagService.get_flag_by_id(flag_id, db)
        return UrlFlagModel.model_validate(flag)

    @classmethod
    def get_all_flags(cls, db: Session, skip: int = 0, limit: int = 100) -> List[UrlFlagModel]:
        flags = UrlFlagService.get_all_flags(db, skip, limit)
        return [UrlFlagModel.model_validate(f) for f in flags]

    @classmethod
    def get_user_flags(cls, user: User, db: Session, skip: int = 0, limit: int = 100) -> List[UrlFlagModel]:
        flags = UrlFlagService.get_flags_by_user(user.user_id, db, skip, limit)
        return [UrlFlagModel.model_validate(f) for f in flags]


url_flag_control = UrlFlagControl()
