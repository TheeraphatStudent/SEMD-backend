from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func, extract, and_
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import secrets
import hashlib

from models.db import AccessKey, UsageLog, User
from models.access.access_key_request import (
    AccessKeyCreateRequest,
    AccessKeyAdminCreateRequest, AccessKeyAdminUpdateRequest
)
from libs.types.enums import RoleType


class AccessKeyService:

    @staticmethod
    def _generate_access_key() -> tuple[str, str]:
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, key_hash

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @classmethod
    def create_key(cls, user: User, request: AccessKeyCreateRequest, db: Session) -> tuple[AccessKey, str]:
        raw_key, key_hash = cls._generate_access_key()

        expired_at = request.expired_at or (
            datetime.utcnow() + timedelta(days=365))

        new_key = AccessKey(
            user_id=user.user_id,
            key_name=request.key_name,
            access_key_hash=key_hash,
            is_active=True,
            expired_at=expired_at
        )

        db.add(new_key)
        db.commit()
        db.refresh(new_key)

        return new_key, raw_key

    @classmethod
    def reset_key(cls, user: User, key_id: int, db: Session) -> tuple[AccessKey, str]:
        old_key = db.query(AccessKey).filter(
            AccessKey.access_key_id == key_id,
            AccessKey.user_id == user.user_id
        ).first()

        if not old_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Access key with id {key_id} not found"
            )

        old_key.is_active = False
        old_key.updated_at = datetime.utcnow()

        raw_key, key_hash = cls._generate_access_key()
        expired_at = datetime.utcnow() + timedelta(days=365)

        new_key = AccessKey(
            user_id=user.user_id,
            key_name=old_key.key_name,
            access_key_hash=key_hash,
            is_active=True,
            usage_limit=old_key.usage_limit,
            expired_at=expired_at
        )

        db.add(new_key)
        db.commit()
        db.refresh(new_key)

        return new_key, raw_key

    @classmethod
    def get_user_keys(cls, user: User, db: Session, skip: int = 0, limit: int = 100) -> List[AccessKey]:
        return db.query(AccessKey).filter(
            AccessKey.user_id == user.user_id
        ).order_by(AccessKey.created_at.desc()).offset(skip).limit(limit).all()

    @classmethod
    def count_user_keys(cls, user: User, db: Session) -> int:
        return db.query(func.count(AccessKey.access_key_id)).filter(
            AccessKey.user_id == user.user_id
        ).scalar()

    @classmethod
    def get_key_by_id(cls, key_id: int, db: Session) -> AccessKey:
        key = db.query(AccessKey).filter(
            AccessKey.access_key_id == key_id).first()
        if not key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Access key with id {key_id} not found"
            )
        return key

    @classmethod
    def get_key_usage_monthly(cls, key_id: int, year: int, month: int, db: Session) -> Dict[str, Any]:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        daily_usage = db.query(
            func.date(UsageLog.created_at).label('date'),
            func.count(UsageLog.usage_log_id).label('count')
        ).filter(
            UsageLog.access_key_id == key_id,
            UsageLog.created_at >= start_date,
            UsageLog.created_at < end_date
        ).group_by(func.date(UsageLog.created_at)).all()

        daily_data = {str(row.date): row.count for row in daily_usage}

        counts = [row.count for row in daily_usage]
        total = sum(counts) if counts else 0
        avg_per_day = total / len(counts) if counts else 0
        max_per_day = max(counts) if counts else 0

        return {
            'year': year,
            'month': month,
            'daily_usage': daily_data,
            'total': total,
            'avg_per_day': round(avg_per_day, 2),
            'max_per_day': max_per_day,
            'days_with_usage': len(counts)
        }

    @classmethod
    def get_key_usage_yearly(cls, key_id: int, year: int, db: Session) -> Dict[str, Any]:
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)

        monthly_usage = db.query(
            extract('month', UsageLog.created_at).label('month'),
            func.count(UsageLog.usage_log_id).label('count')
        ).filter(
            UsageLog.access_key_id == key_id,
            UsageLog.created_at >= start_date,
            UsageLog.created_at < end_date
        ).group_by(extract('month', UsageLog.created_at)).all()

        monthly_data = {int(row.month): row.count for row in monthly_usage}

        counts = [row.count for row in monthly_usage]
        total = sum(counts) if counts else 0
        avg_per_month = total / len(counts) if counts else 0
        max_per_month = max(counts) if counts else 0

        return {
            'year': year,
            'monthly_usage': monthly_data,
            'total': total,
            'avg_per_month': round(avg_per_month, 2),
            'max_per_month': max_per_month,
            'months_with_usage': len(counts)
        }

    @classmethod
    def get_key_usage_all_time(cls, key_id: int, db: Session) -> Dict[str, Any]:
        yearly_usage = db.query(
            extract('year', UsageLog.created_at).label('year'),
            func.count(UsageLog.usage_log_id).label('count')
        ).filter(
            UsageLog.access_key_id == key_id
        ).group_by(extract('year', UsageLog.created_at)).all()

        yearly_data = {int(row.year): row.count for row in yearly_usage}

        total = sum(row.count for row in yearly_usage)

        first_usage = db.query(func.min(UsageLog.created_at)).filter(
            UsageLog.access_key_id == key_id
        ).scalar()

        last_usage = db.query(func.max(UsageLog.created_at)).filter(
            UsageLog.access_key_id == key_id
        ).scalar()

        return {
            'yearly_usage': yearly_data,
            'total': total,
            'first_usage': first_usage.isoformat() if first_usage else None,
            'last_usage': last_usage.isoformat() if last_usage else None
        }

    @classmethod
    def admin_create_key(cls, request: AccessKeyAdminCreateRequest, db: Session) -> tuple[AccessKey, str]:
        user = db.query(User).filter(User.user_id == request.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {request.user_id} not found"
            )

        raw_key, key_hash = cls._generate_access_key()
        expired_at = request.expired_at or (
            datetime.utcnow() + timedelta(days=365))

        new_key = AccessKey(
            user_id=request.user_id,
            key_name=request.key_name,
            access_key_hash=key_hash,
            is_active=True,
            usage_limit=request.usage_limit,
            expired_at=expired_at
        )

        db.add(new_key)
        db.commit()
        db.refresh(new_key)

        return new_key, raw_key

    @classmethod
    def admin_update_key(cls, key_id: int, request: AccessKeyAdminUpdateRequest, db: Session) -> AccessKey:
        key = db.query(AccessKey).filter(
            AccessKey.access_key_id == key_id).first()

        if not key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Access key with id {key_id} not found"
            )

        if request.key_name is not None:
            key.key_name = request.key_name
        if request.usage_limit is not None:
            key.usage_limit = request.usage_limit
        if request.is_active is not None:
            key.is_active = request.is_active
        if request.expired_at is not None:
            key.expired_at = request.expired_at

        key.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(key)

        return key

    @classmethod
    def admin_delete_key(cls, key_id: int, db: Session) -> bool:
        key = db.query(AccessKey).filter(
            AccessKey.access_key_id == key_id).first()

        if not key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Access key with id {key_id} not found"
            )

        db.delete(key)
        db.commit()

        return True

    @classmethod
    def get_all_keys(cls, db: Session, skip: int = 0, limit: int = 100) -> List[AccessKey]:
        return db.query(AccessKey).order_by(AccessKey.created_at.desc()).offset(skip).limit(limit).all()

    @classmethod
    def count_all_keys(cls, db: Session) -> int:
        return db.query(func.count(AccessKey.access_key_id)).scalar()

    @classmethod
    def get_key_current_usage(cls, key_id: int, db: Session) -> int:
        return db.query(func.count(UsageLog.usage_log_id)).filter(
            UsageLog.access_key_id == key_id
        ).scalar() or 0


access_key_service = AccessKeyService()
