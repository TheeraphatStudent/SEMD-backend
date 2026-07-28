"""Authorization bypass in PredictionService.predict_with_service.

`/prediction/predict` was changed to accept anonymous callers (`user_id=None`)
so the browser extension can call it without a session. The ownership check in
`services/prediction_service.py` read:

    if user_id and service_conf.user_id and service_conf.user_id != user_id:

The leading `user_id and` made the entire condition short-circuit to False
whenever `user_id` was None -- i.e. exactly for the newly-allowed anonymous
callers. Net effect: an unauthenticated caller could pass ANY `service_id` and
use that ServiceConf regardless of owner, where an authenticated non-owner got
a 403. For `service_type=REST_API` that means spending another user's
third-party API quota using their stored credentials
(`ThirdServiceConf.headers_json`), plus enumerating valid service ids via the
404-vs-200 difference.

These tests pin the fixed semantics:

    caller       config owner        -> outcome
    anonymous    MEMBER-owned        -> 403
    anonymous    ADMIN-owned         -> allowed (shared/system service)
    anonymous    owner-less (NULL)   -> allowed
    non-owner    MEMBER-owned        -> 403
    owner        MEMBER-owned        -> allowed

The ADMIN-owned row matters as much as the 403 rows: it is what stops a future
"simplify this check" pass from deleting the owner-role branch and silently
403-ing every anonymous extension call.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from libs.types.enums import RoleType, ServiceType
from services.prediction_service import PredictionService

MEMBER_OWNER_ID = 100
ADMIN_OWNER_ID = 7
OTHER_USER_ID = 999


class _QueuedAsyncSession:
    """Async session stub that returns queued rows in order.

    `predict_with_service` executes up to two statements on the deny path --
    first the ServiceConf lookup, then the owner User lookup -- so a
    single-fixed-value fake (like test_prediction_ssrf.py's) is not enough.
    """

    def __init__(self, rows):
        self._rows = list(rows)
        self.calls = 0

    async def execute(self, _stmt):
        self.calls += 1
        row = self._rows.pop(0) if self._rows else None
        return SimpleNamespace(scalar_one_or_none=lambda: row)


def _service_conf(owner_id, service_id=42):
    return SimpleNamespace(
        service_conf_id=service_id,
        service_name='private-service',
        service_type=ServiceType.ML_MODEL.value,
        user_id=owner_id,
        is_active=True,
    )


def _user(user_id, role):
    return SimpleNamespace(user_id=user_id, role=role)


class PredictionServiceOwnershipTests(unittest.IsolatedAsyncioTestCase):

    async def _predict(self, rows, user_id):
        service = PredictionService(_QueuedAsyncSession(rows))
        with patch.object(
            service, '_predict_with_ml_model', new=AsyncMock(return_value=[{'ok': True}])
        ) as dispatch:
            result = await service.predict_with_service(
                service_id=42, urls=['https://example.com'], user_id=user_id
            )
        return result, dispatch

    async def _assert_denied(self, rows, user_id):
        service = PredictionService(_QueuedAsyncSession(rows))
        with patch.object(service, '_predict_with_ml_model', new=AsyncMock()) as dispatch:
            with self.assertRaises(HTTPException) as ctx:
                await service.predict_with_service(
                    service_id=42, urls=['https://example.com'], user_id=user_id
                )
        dispatch.assert_not_called()
        return ctx.exception

    async def test_anonymous_caller_denied_another_users_service_conf(self):
        """The bypass itself: user_id=None must NOT skip the ownership check."""
        exc = await self._assert_denied(
            [_service_conf(MEMBER_OWNER_ID), _user(MEMBER_OWNER_ID, RoleType.MEMBER.value)],
            user_id=None,
        )
        self.assertEqual(exc.status_code, 403)
        self.assertEqual(exc.detail, 'Access denied to this service configuration')

    async def test_authenticated_non_owner_denied_identically(self):
        """Anonymous and authenticated-non-owner must reach the same verdict."""
        exc = await self._assert_denied(
            [_service_conf(MEMBER_OWNER_ID), _user(MEMBER_OWNER_ID, RoleType.MEMBER.value)],
            user_id=OTHER_USER_ID,
        )
        self.assertEqual(exc.status_code, 403)

    async def test_anonymous_and_non_owner_get_the_same_status_code(self):
        anon = await self._assert_denied(
            [_service_conf(MEMBER_OWNER_ID), _user(MEMBER_OWNER_ID, RoleType.MEMBER.value)],
            user_id=None,
        )
        authed = await self._assert_denied(
            [_service_conf(MEMBER_OWNER_ID), _user(MEMBER_OWNER_ID, RoleType.MEMBER.value)],
            user_id=OTHER_USER_ID,
        )
        self.assertEqual((anon.status_code, anon.detail), (authed.status_code, authed.detail))

    async def test_owner_still_allowed(self):
        _, dispatch = await self._predict(
            [_service_conf(MEMBER_OWNER_ID)], user_id=MEMBER_OWNER_ID
        )
        dispatch.assert_called_once()

    async def test_anonymous_allowed_on_ownerless_service_conf(self):
        """`user_id IS NULL` on the config == shared/system service, stays open."""
        _, dispatch = await self._predict([_service_conf(None)], user_id=None)
        dispatch.assert_called_once()

    async def test_anonymous_allowed_on_admin_owned_service_conf(self):
        """Admin-owned config is the 'system service' escape hatch the browser
        extension depends on -- deleting the owner-role branch must fail here."""
        _, dispatch = await self._predict(
            [_service_conf(ADMIN_OWNER_ID), _user(ADMIN_OWNER_ID, RoleType.ADMIN.value)],
            user_id=None,
        )
        dispatch.assert_called_once()

    async def test_anonymous_allowed_on_super_admin_owned_service_conf(self):
        _, dispatch = await self._predict(
            [_service_conf(ADMIN_OWNER_ID), _user(ADMIN_OWNER_ID, RoleType.SUPER_ADMIN.value)],
            user_id=None,
        )
        dispatch.assert_called_once()

    async def test_missing_owner_row_denies_rather_than_falls_open(self):
        exc = await self._assert_denied([_service_conf(MEMBER_OWNER_ID), None], user_id=None)
        self.assertEqual(exc.status_code, 403)

    async def test_missing_service_conf_still_404s_for_anonymous(self):
        service = PredictionService(_QueuedAsyncSession([None]))
        with self.assertRaises(HTTPException) as ctx:
            await service.predict_with_service(
                service_id=42, urls=['https://example.com'], user_id=None
            )
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == '__main__':
    unittest.main()
