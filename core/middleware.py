"""Request-ID + access-log middleware.

Generates (or passes through an inbound `X-Request-ID`), attaches it to
`request.state.request_id` so route handlers and error handlers can read it,
echoes it back as a response header, and emits one structured access-log line
per request (method, path, status, duration_ms, request_id -- no headers, no
body, no query string, to avoid logging tokens/secrets passed as params).
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger('semd.access')

REQUEST_ID_HEADER = 'X-Request-ID'


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            'request completed',
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
            },
        )
        return response
