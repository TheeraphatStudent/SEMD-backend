"""Structured logging setup.

Emits one JSON line per log record, so request-scoped fields (request_id,
method, path, status, duration_ms) show up as queryable structure instead of
free-text. Must never receive passwords, JWTs, refresh tokens, TOTP secrets,
OAuth tokens, API keys, or Access Codes in `extra` -- see
docs/backend/SEMD_BACKEND_CURRENT_STATE.md Security Audit for what NOT to log.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

_RESERVED_LOG_RECORD_ATTRS = frozenset(logging.LogRecord(
    '', 0, '', 0, '', (), None
).__dict__.keys())


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_ATTRS and key not in payload:
                payload[key] = value
        if record.exc_info:
            payload['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = 'INFO') -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
