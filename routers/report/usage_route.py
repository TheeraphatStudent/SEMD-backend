from routers import BaseRoute
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from guard.auth_guard import AuthGuard, get_async_db
from database import User, UsageLog, Prediction, ServiceConf


class UsageLogResponse(BaseModel):
    usage_log_id: int
    service_id: Optional[int]
    service_name: Optional[str]
    prediction_id: Optional[int]
    url: Optional[str]
    is_malicious: Optional[bool]
    type: str
    created_at: datetime

    class Config:
        from_attributes = True


class RecentActivityResponse(BaseModel):
    url: str
    verdict: str 
    time: str
    prediction_id: Optional[int]


class UsageStatsResponse(BaseModel):
    total_predictions: int
    safe_count: int
    danger_count: int
    today_count: int
    this_week_count: int
    this_month_count: int


class UsageRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/report/usage",
            tags=["usage-log"],
            responses={404: {"description": "Not found"}, 401: {"description": "Unauthorized"}}
        )

        self.router.get(
            "/logs",
            response_model=List[UsageLogResponse],
            summary="Get Usage Logs",
            description="Get usage logs for the current user"
        )(self.get_usage_logs)

        self.router.get(
            "/recent",
            response_model=List[RecentActivityResponse],
            summary="Get Recent Activity",
            description="Get recent prediction activity for the current user"
        )(self.get_recent_activity)

        self.router.get(
            "/stats",
            response_model=UsageStatsResponse,
            summary="Get Usage Stats",
            description="Get usage statistics for the current user"
        )(self.get_usage_stats)

    async def get_usage_logs(
        self,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db),
        limit: int = Query(default=50, le=100),
        offset: int = Query(default=0, ge=0)
    ) -> List[UsageLogResponse]:
        # Get usage logs with prediction and service info
        stmt = (
            select(
                UsageLog,
                Prediction.url,
                Prediction.is_malicious,
                ServiceConf.service_name
            )
            .outerjoin(Prediction, UsageLog.prediction_id == Prediction.prediction_id)
            .outerjoin(ServiceConf, UsageLog.service_id == ServiceConf.service_conf_id)
            .where(Prediction.user_id == current_user.user_id)
            .order_by(desc(UsageLog.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(stmt)
        rows = result.all()

        return [
            UsageLogResponse(
                usage_log_id=row.UsageLog.usage_log_id,
                service_id=row.UsageLog.service_id,
                service_name=row.service_name,
                prediction_id=row.UsageLog.prediction_id,
                url=row.url,
                is_malicious=row.is_malicious,
                type=row.UsageLog.type,
                created_at=row.UsageLog.created_at
            )
            for row in rows
        ]

    async def get_recent_activity(
        self,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db),
        limit: int = Query(default=10, le=50)
    ) -> List[RecentActivityResponse]:
        # Get recent predictions for the user
        stmt = (
            select(Prediction)
            .where(Prediction.user_id == current_user.user_id)
            .order_by(desc(Prediction.created_at))
            .limit(limit)
        )

        result = await db.execute(stmt)
        predictions = result.scalars().all()

        def format_time(dt: datetime) -> str:
            now = datetime.utcnow()
            diff = now - dt.replace(tzinfo=None) if dt.tzinfo else now - dt
            
            if diff.days > 0:
                return f"{diff.days} วันที่แล้ว"
            elif diff.seconds >= 3600:
                hours = diff.seconds // 3600
                return f"{hours} ชม.ที่แล้ว"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                return f"{minutes} นาทีที่แล้ว"
            else:
                return "เมื่อสักครู่"

        def get_verdict(is_malicious: bool) -> str:
            return 'Danger' if is_malicious else 'Safe'

        return [
            RecentActivityResponse(
                url=p.url,
                verdict=get_verdict(p.is_malicious),
                time=format_time(p.created_at),
                prediction_id=p.prediction_id
            )
            for p in predictions
        ]

    async def get_usage_stats(
        self,
        current_user: User = Depends(AuthGuard.get_current_user),
        db: AsyncSession = Depends(get_async_db)
    ) -> UsageStatsResponse:
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = today_start.replace(day=1)

        # Total predictions
        total_stmt = select(func.count()).select_from(Prediction).where(
            Prediction.user_id == current_user.user_id
        )
        total_result = await db.execute(total_stmt)
        total_predictions = total_result.scalar() or 0

        # Safe count
        safe_stmt = select(func.count()).select_from(Prediction).where(
            Prediction.user_id == current_user.user_id,
            Prediction.is_malicious == False
        )
        safe_result = await db.execute(safe_stmt)
        safe_count = safe_result.scalar() or 0

        # Danger count
        danger_count = total_predictions - safe_count

        # Today count
        today_stmt = select(func.count()).select_from(Prediction).where(
            Prediction.user_id == current_user.user_id,
            Prediction.created_at >= today_start
        )
        today_result = await db.execute(today_stmt)
        today_count = today_result.scalar() or 0

        # This week count
        week_stmt = select(func.count()).select_from(Prediction).where(
            Prediction.user_id == current_user.user_id,
            Prediction.created_at >= week_start
        )
        week_result = await db.execute(week_stmt)
        this_week_count = week_result.scalar() or 0

        # This month count
        month_stmt = select(func.count()).select_from(Prediction).where(
            Prediction.user_id == current_user.user_id,
            Prediction.created_at >= month_start
        )
        month_result = await db.execute(month_stmt)
        this_month_count = month_result.scalar() or 0

        return UsageStatsResponse(
            total_predictions=total_predictions,
            safe_count=safe_count,
            danger_count=danger_count,
            today_count=today_count,
            this_week_count=this_week_count,
            this_month_count=this_month_count
        )
