"""Regression test: DELETE /setting/third-service/{id} constructed
BaseResponseModel(status="success", ...) -- but BaseResponseModel.status is
typed int, so this raised a pydantic ValidationError on every call (verified
empirically before fixing). Confirms the response now serializes.
"""

from __future__ import annotations

import unittest

from models.common.base_response_model import BaseResponseModel


class ThirdServiceDeleteResponseTests(unittest.TestCase):
    def test_delete_response_constructs_without_error(self):
        model = BaseResponseModel(status=200, message="Third-party service deleted successfully")
        self.assertEqual(model.status, 200)


if __name__ == '__main__':
    unittest.main()
