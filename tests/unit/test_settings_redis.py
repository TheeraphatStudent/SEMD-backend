from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from config.settings import Settings, config as ini_config

# backend.ini's [REDIS] section, as actually read from disk -- used as the "known ini value"
# baseline so these tests keep working if backend.ini's values ever change.
_INI_HOST = ini_config.get('REDIS', 'HOST', fallback='localhost')
_INI_PASSWORD = ini_config.get('REDIS', 'PASSWORD', fallback='')
_INI_PORT = ini_config.getint('REDIS', 'PORT', fallback=6379)
_INI_DB = ini_config.getint('REDIS', 'DB', fallback=0)


class RedisSettingsPrecedenceTests(unittest.TestCase):
    def test_env_var_overrides_ini(self):
        with patch.dict(os.environ, {'REDIS_HOST': 'redis'}, clear=False):
            self.assertEqual(Settings().redis_host, 'redis')

    def test_ini_used_when_env_absent(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('REDIS_HOST', None)
            self.assertEqual(Settings().redis_host, _INI_HOST)

    def test_blank_env_does_not_erase_valid_ini_password(self):
        with patch.dict(os.environ, {'REDIS_PASSWORD': ''}, clear=False):
            self.assertEqual(Settings().redis_password, _INI_PASSWORD)

    def test_port_and_db_parsed_as_int(self):
        with patch.dict(os.environ, {'REDIS_PORT': '6390', 'REDIS_DB': '2'}, clear=False):
            s = Settings()
            self.assertEqual(s.redis_port, 6390)
            self.assertIsInstance(s.redis_port, int)
            self.assertEqual(s.redis_db, 2)
            self.assertIsInstance(s.redis_db, int)

    def test_ini_port_and_db_are_also_ints(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('REDIS_PORT', None)
            os.environ.pop('REDIS_DB', None)
            s = Settings()
            self.assertEqual(s.redis_port, _INI_PORT)
            self.assertEqual(s.redis_db, _INI_DB)

    def test_password_not_printed_when_settings_constructed(self):
        secret = 'do-not-leak-me'
        buf = io.StringIO()
        with patch.dict(os.environ, {'REDIS_PASSWORD': secret}, clear=False):
            with redirect_stdout(buf):
                Settings()
        self.assertNotIn(secret, buf.getvalue())


def _fresh_client_with_settings(overrides: dict):
    """Build a RedisClient bound to a freshly-constructed Settings() reflecting `overrides`,
    bypassing the process-wide cached `config.settings.settings` singleton (which is built once
    at first import and would otherwise ignore env changes made after that)."""
    from services.client.redis_client import RedisClient

    with patch.dict(os.environ, overrides, clear=False):
        fresh_settings = Settings()

    RedisClient._instance = None
    with patch('services.client.redis_client.settings', fresh_settings):
        client = RedisClient()
    RedisClient._instance = None
    return client


class RedisLiveConnectionTests(unittest.TestCase):
    """Live-Redis checks; self-skip if the shared Redis isn't reachable in this environment."""

    @classmethod
    def setUpClass(cls):
        try:
            _fresh_client_with_settings({}).client.ping()
        except Exception as exc:  # pragma: no cover - environment dependent
            raise unittest.SkipTest(f"Live Redis not reachable: {exc}")

    def test_invalid_password_fails_with_actionable_error(self):
        import redis

        client = _fresh_client_with_settings({'REDIS_PASSWORD': 'definitely-wrong-password'})
        with self.assertRaises(redis.exceptions.AuthenticationError):
            client.client.ping()

    def test_unavailable_redis_fails_without_hanging(self):
        import time
        import redis

        client = _fresh_client_with_settings({'REDIS_HOST': '127.0.0.1', 'REDIS_PORT': '59999'})
        start = time.monotonic()
        with self.assertRaises(redis.exceptions.ConnectionError):
            client.client.ping()
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 10, "connection attempt should fail fast via socket_connect_timeout")


if __name__ == '__main__':
    unittest.main()
