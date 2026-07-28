from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core.exceptions import PermissionDeniedError
from models.db import UrlFlag, User
from libs.types.enums import ACLType, RoleType
from models.report.url_flag_request import UrlFlagCreateRequest, UrlFlagUpdateRequest

_ADMIN_ROLES = (RoleType.ADMIN.value, RoleType.SUPER_ADMIN.value)


class UrlFlagService:

    @classmethod
    def create_flag(cls, user: User, request: UrlFlagCreateRequest, db: Session) -> UrlFlag:
        # GLOBAL flags are applied to every user's prediction result (see
        # check_url_flag/check_url_flag_async below) -- previously any
        # authenticated MEMBER could create one, meaning any account could
        # unilaterally whitelist a malicious URL or blacklist a legitimate
        # one for the entire user base. See
        # docs/backend/features/url-flags-whitelist/README.md.
        if request.access_level == ACLType.GLOBAL and user.role not in _ADMIN_ROLES:
            raise PermissionDeniedError('Only an admin can create a GLOBAL-access-level flag')

        new_flag = UrlFlag(
            user_id=user.user_id,
            url=request.url,
            type=request.type.value,
            access_level=request.access_level.value
        )

        db.add(new_flag)
        db.commit()
        db.refresh(new_flag)

        return new_flag

    @classmethod
    def update_flag(cls, user: User, flag_id: int, request: UrlFlagUpdateRequest, db: Session) -> UrlFlag:
        flag = db.query(UrlFlag).filter(UrlFlag.url_flag_id == flag_id).first()

        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"URL Flag with id {flag_id} not found"
            )

        is_owner = flag.user_id == user.user_id
        is_admin = user.role in _ADMIN_ROLES

        if not is_owner and not is_admin:
            raise PermissionDeniedError("You don't have permission to update this flag")

        # Admin-only if the flag is (or is being made) GLOBAL -- same
        # reasoning as create_flag above. Covers both "promote my private
        # flag to global" and "edit an existing global flag".
        resulting_access_level = request.access_level.value if request.access_level is not None else flag.access_level
        if resulting_access_level == ACLType.GLOBAL.value and not is_admin:
            raise PermissionDeniedError('Only an admin can set or modify a GLOBAL-access-level flag')

        if request.url is not None:
            flag.url = request.url
        if request.type is not None:
            flag.type = request.type.value
        if request.access_level is not None:
            flag.access_level = request.access_level.value

        flag.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(flag)

        return flag

    @classmethod
    def delete_flag(cls, user: User, flag_id: int, db: Session) -> bool:
        flag = db.query(UrlFlag).filter(UrlFlag.url_flag_id == flag_id).first()

        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"URL Flag with id {flag_id} not found"
            )

        is_owner = flag.user_id == user.user_id
        is_admin = user.role in _ADMIN_ROLES

        # Admin override added: previously an admin could not remove a rogue
        # GLOBAL flag created by another user -- only the original creator
        # could delete it, which is exactly backwards for a flag type that's
        # meant to be admin-governed.
        if not is_owner and not is_admin:
            raise PermissionDeniedError("You don't have permission to delete this flag")

        db.delete(flag)
        db.commit()

        return True

    @classmethod
    def get_flag_by_id(cls, flag_id: int, db: Session) -> UrlFlag:
        flag = db.query(UrlFlag).filter(UrlFlag.url_flag_id == flag_id).first()

        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"URL Flag with id {flag_id} not found"
            )

        return flag

    @classmethod
    def get_all_flags(cls, db: Session, skip: int = 0, limit: int = 100) -> List[UrlFlag]:
        return db.query(UrlFlag).offset(skip).limit(limit).all()

    @classmethod
    def get_flags_by_user(cls, user_id: int, db: Session, skip: int = 0, limit: int = 100) -> List[UrlFlag]:
        return db.query(UrlFlag).filter(UrlFlag.user_id == user_id).offset(skip).limit(limit).all()

    @classmethod
    def check_url_flag(cls, url: str, user_id: Optional[int], db: Session) -> Optional[UrlFlag]:
        query = db.query(UrlFlag).filter(UrlFlag.url == url)

        if user_id:
            query = query.filter(
                or_(
                    UrlFlag.access_level == ACLType.GLOBAL.value,
                    UrlFlag.user_id == user_id
                )
            )
        else:
            query = query.filter(UrlFlag.access_level == ACLType.GLOBAL.value)

        return query.first()

    @classmethod
    async def check_url_flag_async(cls, url: str, user_id: Optional[int], db: AsyncSession) -> Optional[UrlFlag]:
        from sqlalchemy import text
        
        if user_id:
            stmt = select(UrlFlag).where(
                UrlFlag.url == url,
                or_(
                    UrlFlag.access_level.cast(db.bind.dialect.name == 'postgresql' and 'text' or None) == ACLType.GLOBAL.value if False else text("access_level::text = 'GLOBAL'"),
                    UrlFlag.user_id == user_id
                )
            )
        else:
            stmt = select(UrlFlag).where(
                UrlFlag.url == url,
                text("access_level::text = 'GLOBAL'")
            )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()


url_flag_service = UrlFlagService()
