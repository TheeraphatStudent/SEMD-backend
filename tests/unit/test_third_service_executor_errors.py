"""Domain 6: ThirdServiceExecutor error handling.

Before this change, connection errors and vendor response bodies were put
directly into the raised HTTPException's `detail` via `str(e)`/
`e.response.text`. This executor is called both from the admin "test
connection" endpoint AND from services/prediction_service.py's
_predict_with_third_party -- meaning any authenticated MEMBER submitting a
prediction against a REST_API-type service could see raw connection-error
text and vendor response bodies about an admin-configured integration they
don't own. Fixed: real detail logged server-side, generic AppError to the
caller.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from core.exceptions import ExternalServiceError, ServiceUnavailableError
from services.client.third_service_executor import ThirdServiceExecutor


def _fake_conf():
    return SimpleNamespace(
        base_url='https://vendor.example.com/scan',
        http_method='GET',
        headers_json={},
        config_json={},
    )


class ThirdServiceExecutorErrorTests(unittest.IsolatedAsyncioTestCase):
    async def test_http_status_error_does_not_leak_vendor_response_body(self):
        executor = ThirdServiceExecutor(_fake_conf())
        request = httpx.Request('GET', 'https://vendor.example.com/scan')
        response = httpx.Response(
            502, request=request, content=b'{"internal_debug": "vendor_api_key=SECRET123"}'
        )

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch('httpx.AsyncClient', return_value=mock_client):
            with self.assertRaises(ExternalServiceError) as ctx:
                await executor.execute({})

        self.assertNotIn('SECRET123', ctx.exception.detail)
        self.assertNotIn('vendor_api_key', ctx.exception.detail)
        self.assertEqual(ctx.exception.code, 'THIRD_PARTY_ERROR')

    async def test_connection_error_does_not_leak_exception_text(self):
        executor = ThirdServiceExecutor(_fake_conf())
        mock_client = MagicMock()
        mock_client.request = AsyncMock(
            side_effect=httpx.ConnectError('Connection refused to 10.0.0.5:8443 (internal-vendor-proxy)')
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch('httpx.AsyncClient', return_value=mock_client):
            with self.assertRaises(ServiceUnavailableError) as ctx:
                await executor.execute({})

        self.assertNotIn('10.0.0.5', ctx.exception.detail)
        self.assertNotIn('internal-vendor-proxy', ctx.exception.detail)

    async def test_redirect_is_rejected_not_followed(self):
        executor = ThirdServiceExecutor(_fake_conf())
        request = httpx.Request('GET', 'https://vendor.example.com/scan')
        response = httpx.Response(
            302, request=request, headers={'location': 'http://169.254.169.254/'}
        )

        mock_client = MagicMock()
        mock_client.request = AsyncMock(return_value=response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch('httpx.AsyncClient', return_value=mock_client) as client_cls:
            with self.assertRaises(Exception):
                await executor.execute({})

        # follow_redirects=False passed explicitly to the client constructor.
        _, kwargs = client_cls.call_args
        self.assertFalse(kwargs.get('follow_redirects', True))


if __name__ == '__main__':
    unittest.main()
