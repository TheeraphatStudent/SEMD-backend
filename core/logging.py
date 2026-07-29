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
import re
import sys
from datetime import datetime, timezone

_RESERVED_LOG_RECORD_ATTRS = frozenset(logging.LogRecord(
    '', 0, '', 0, '', (), None
).__dict__.keys())
_URL_PATTERN = re.compile(r'https?://[^\s\]\[\)\}\>,\"\']+')
_URL_FIELD_NAMES = frozenset({'url', 'urls', 'target_url', 'url_list'})
_SECRET_FIELD_PARTS = ('password', 'token', 'secret',
                       'api_key', 'authorization', 'cookie')


def _redact_log_value(value, field_name: str | None = None):
    """Remove submitted URLs and secret-like values before JSON encoding."""
    normalized_name = (field_name or '').lower()
    if normalized_name in _URL_FIELD_NAMES:
        if isinstance(value, (list, tuple, set)):
            return f'[REDACTED_URLS:{len(value)}]'
        return '[REDACTED_URL]'
    if any(part in normalized_name for part in _SECRET_FIELD_PARTS):
        return '[REDACTED]'
    if isinstance(value, str):
        return _URL_PATTERN.sub('[REDACTED_URL]', value)
    if isinstance(value, dict):
        return {key: _redact_log_value(item, key) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_redact_log_value(item) for item in value]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': _redact_log_value(record.getMessage()),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_ATTRS and key not in payload:
                payload[key] = _redact_log_value(value, key)
        if record.exc_info:
            payload['exc_info'] = _redact_log_value(
                self.formatException(record.exc_info))
        return json.dumps(payload, default=str)


def configure_logging(level: str = 'INFO') -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
