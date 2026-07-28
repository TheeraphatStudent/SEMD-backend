"""Liveness/readiness endpoints.

`GET /health` (main app root) returns static placeholder data and does not
check dependencies -- see SEMD_BACKEND_CURRENT_STATE.md section 2. These two
new endpoints are additive, not a replacement for it in this pass:

- `/health/live`: process is running, no dependency calls. Always 200 once
  the ASGI server is accepting connections.
- `/health/ready`: checks Postgres and Redis reachability with a short
  timeout. Does not check optional third-party detectors -- per the mandate,
  readiness should not depend on services that aren't required for every
  request.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter
from sqlalchemy import text
from starlette.responses import JSONResponse

from services.client.postgres_client import postgres_client
from services.client.redis_client import redis_client

router = APIRouter(prefix='/health', tags=['health'])

_READY_CHECK_TIMEOUT_SECONDS = 3


async def _check_database() -> bool:
    try:
        async def _ping():
            async with postgres_client.get_async_session() as session:
                await session.execute(text('SELECT 1'))
        await asyncio.wait_for(_ping(), timeout=_READY_CHECK_TIMEOUT_SECONDS)
        return True
    except Exception:
        return False


async def _check_redis() -> bool:
    try:
        await asyncio.wait_for(
            asyncio.to_thread(redis_client.client.ping),
            timeout=_READY_CHECK_TIMEOUT_SECONDS,
        )
        return True
    except Exception:
        return False


@router.get('/live')
async def liveness():
    return {'status': 'live'}


@router.get('/ready')
async def readiness():
    database_ok, redis_ok = await asyncio.gather(_check_database(), _check_redis())
    checks = {'database': database_ok, 'redis': redis_ok}
    all_ok = all(checks.values())
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={'status': 'ready' if all_ok else 'not_ready', 'checks': checks},
    )
