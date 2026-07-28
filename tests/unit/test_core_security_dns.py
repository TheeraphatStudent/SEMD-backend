"""DNS-resolution layer of the SSRF validator (Domain 5).

Mocks `getaddrinfo` for the hostname-resolution cases so this suite doesn't
depend on live DNS/network access (the literal-IP cases in
test_core_security.py already cover the no-DNS-needed paths without mocking).
A codebase-wide note: `tests/unit/test_ml_prediction_service.py` and
`test_prediction_ssrf.py` DO exercise a real DNS lookup for "example.com"
through the full call path -- verified fast (<100ms) in this environment, but
that is a live network dependency worth being aware of if this suite ever
runs in a fully offline CI runner.
"""

from __future__ import annotations

import socket
import unittest
from unittest.mock import AsyncMock, patch

from core.security import check_url_safety_async, resolve_and_check_dns


def _addrinfo(ip: str, family=socket.AF_INET):
    return [(family, socket.SOCK_STREAM, 6, '', (ip, 0))]


class DnsResolutionSafetyTests(unittest.IsolatedAsyncioTestCase):
    async def test_resolves_to_private_ip_is_blocked(self):
        with patch(
            'asyncio.get_running_loop',
            return_value=type('L', (), {'getaddrinfo': AsyncMock(return_value=_addrinfo('10.0.0.5'))})(),
        ):
            blocked, reason = await resolve_and_check_dns('internal.example.com')
        self.assertTrue(blocked)
        self.assertIn('10.0.0.5', reason)

    async def test_resolves_to_public_ip_is_allowed(self):
        with patch(
            'asyncio.get_running_loop',
            return_value=type('L', (), {'getaddrinfo': AsyncMock(return_value=_addrinfo('93.184.216.34'))})(),
        ):
            blocked, _ = await resolve_and_check_dns('public.example.com')
        self.assertFalse(blocked)

    async def test_resolution_failure_is_treated_as_blocked(self):
        loop = type('L', (), {'getaddrinfo': AsyncMock(side_effect=socket.gaierror('not found'))})()
        with patch('asyncio.get_running_loop', return_value=loop):
            blocked, reason = await resolve_and_check_dns('does-not-resolve.invalid')
        self.assertTrue(blocked)
        self.assertIn('failed', reason)

    async def test_check_url_safety_async_rejects_dns_rebound_host(self):
        loop = type('L', (), {'getaddrinfo': AsyncMock(return_value=_addrinfo('169.254.169.254'))})()
        with patch('asyncio.get_running_loop', return_value=loop):
            result = await check_url_safety_async('http://rebinds-to-metadata.example.com/')
        self.assertFalse(result.is_safe)

    async def test_check_url_safety_async_skips_dns_for_literal_ip(self):
        # Should reject on the lexical check alone, no DNS call attempted.
        with patch('asyncio.get_running_loop', side_effect=AssertionError('DNS should not be called')):
            result = await check_url_safety_async('http://127.0.0.1/')
        self.assertFalse(result.is_safe)


if __name__ == '__main__':
    unittest.main()
