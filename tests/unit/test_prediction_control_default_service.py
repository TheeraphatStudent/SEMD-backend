"""PredictionControl._get_default_ml_service must never auto-pick a private
service config.

`services/prediction_service.py::predict_with_service`'s ownership check
(fixed in test_prediction_service_ownership.py) denies anonymous and
non-owning callers a MEMBER-owned ServiceConf. Before this fix,
`_get_default_ml_service` picked the oldest active ML_MODEL row with no
ownership filter at all -- so if that row happened to be MEMBER-owned, every
caller who didn't explicitly pass `service_id` (including every anonymous
extension call, the entire point of keyless prediction) would resolve to a
private config and then immediately 403 against the now-correct ownership
check. This test pins that the SELECT itself only ever returns an
owner-less or admin/super-admin-owned row.
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from control.prediction_control import PredictionControl
from libs.types.enums import RoleType


class _FakeAsyncSession:
    """Returns one queued result per `execute()` call, in order."""

    def __init__(self, rows):
        self._rows = list(rows)

    async def execute(self, _stmt):
        row = self._rows.pop(0) if self._rows else None
        return SimpleNamespace(scalar_one_or_none=lambda: row)


def _service_conf(service_id):
    return SimpleNamespace(service_conf_id=service_id)


class DefaultMlServiceSelectionTests(unittest.IsolatedAsyncioTestCase):

    async def _resolve(self, rows):
        db = _FakeAsyncSession(rows)
        control = PredictionControl(db)
        return await control._get_default_ml_service()

    async def test_returns_the_shared_row_the_query_yields(self):
        """The filtering itself lives in the SQL WHERE clause (outerjoin +
        `user_id IS NULL OR owner role in (ADMIN, SUPER_ADMIN)`), which a
        fake session can't re-execute -- this pins that whatever single row
        the query returns is used as-is, i.e. the function doesn't apply any
        further, separate ownership filtering of its own that could
        re-introduce a mismatch with predict_with_service's check."""
        service_id = await self._resolve([_service_conf(7)])
        self.assertEqual(service_id, 7)

    async def test_no_matching_row_returns_none_rather_than_raising(self):
        service_id = await self._resolve([None])
        self.assertIsNone(service_id)

    async def test_query_filters_on_active_ml_model_and_shared_ownership(self):
        """Static check that the WHERE clause actually expresses the shared-
        ownership condition, since the fake session can't evaluate real SQL."""
        db = _FakeAsyncSession([_service_conf(1)])
        control = PredictionControl(db)
        captured = {}

        async def capture_execute(stmt):
            captured['stmt'] = stmt
            return SimpleNamespace(scalar_one_or_none=lambda: _service_conf(1))

        db.execute = capture_execute
        await control._get_default_ml_service()

        compiled = str(captured['stmt'].compile(compile_kwargs={'literal_binds': True}))
        self.assertIn('is_active', compiled)
        self.assertIn('service_type', compiled)
        self.assertIn('user_id IS NULL', compiled)
        self.assertIn(RoleType.ADMIN.value, compiled)
        self.assertIn(RoleType.SUPER_ADMIN.value, compiled)


if __name__ == '__main__':
    unittest.main()
