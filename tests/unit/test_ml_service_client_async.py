"""Domain 12: get_job_result previously used blocking `time.sleep` in its
poll loop, awaited directly from async FastAPI handlers with no
asyncio.to_thread/run_in_executor wrapper -- meaning every prediction
request blocked the entire ASGI event loop for up to the request timeout
(30-60s), serializing all concurrent request handling in that worker
process. Fixed to use asyncio.sleep. This test proves it: two concurrent
get_job_result calls (each needing ~2 poll cycles before the cache
populates) complete in roughly one poll-cycle's worth of wall-clock time,
not two -- which is only possible if the sleep doesn't block other
coroutines from running.
"""

from __future__ import annotations

import asyncio
import time
import unittest
from unittest.mock import patch

from services.ml_service_client import MLServiceClient


class GetJobResultConcurrencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_polls_do_not_serialize(self):
        client = MLServiceClient()
        call_counts = {'a': 0, 'b': 0}

        def fake_get_cache(cache_key):
            key = 'a' if 'job-a' in cache_key else 'b'
            call_counts[key] += 1
            # Each job "resolves" on its second poll.
            if call_counts[key] >= 2:
                return {'status': 'success', 'job_id': key}
            return None

        with patch('services.ml_service_client.redis_client.get_cache', side_effect=fake_get_cache):
            start = time.perf_counter()
            results = await asyncio.gather(
                client.get_job_result('job-a', timeout=5),
                client.get_job_result('job-b', timeout=5),
            )
            elapsed = time.perf_counter() - start

        self.assertEqual(results[0]['job_id'], 'a')
        self.assertEqual(results[1]['job_id'], 'b')
        # poll_interval is 0.5s; both jobs need one 0.5s sleep before
        # resolving. If sleeps were blocking (serialized), this would take
        # ~1.0s (two sequential half-second blocks). Concurrent: ~0.5s.
        self.assertLess(elapsed, 0.9, 'polls appear to be serialized, not concurrent')

    async def test_get_job_result_returns_none_on_timeout(self):
        client = MLServiceClient()
        with patch('services.ml_service_client.redis_client.get_cache', return_value=None):
            result = await client.get_job_result('never-resolves', timeout=1)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
