import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLServiceClient:

    def __init__(self):
        self.training_queue = 'ml_training_queue'
        self.prediction_queue = 'ml_prediction_queue'
        self.result_queue = 'ml_result_queue'
        self.result_cache_prefix = 'ml_result:'
        self.default_timeout = 30

    def submit_training_job(
        self,
        service_conf_id: int,
        dataset_files: List[str],
        algorithms: Optional[List[str]] = None,
        run_name: Optional[str] = None
    ) -> str:
        job_id = str(uuid.uuid4())

        if algorithms is None:
            algorithms = ['svm', 'xgboost', 'random_forest']

        if run_name is None:
            run_name = f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        job_data = {
            'job_id': job_id,
            'job_type': 'training',
            'service_conf_id': service_conf_id,
            'dataset_files': dataset_files,
            'algorithms': algorithms,
            'run_name': run_name,
            'timestamp': datetime.now().isoformat()
        }

        redis_client.push_to_queue(self.training_queue, job_data)

        logger.info(f"Submitted training job: {job_id}")

        return job_id

    def submit_prediction_job(
        self,
        url: str,
        user_id: Optional[int] = None,
        model_id: Optional[str] = None
    ) -> str:
        job_id = str(uuid.uuid4())

        job_data = {
            'job_id': job_id,
            'job_type': 'prediction',
            'url': url,
            'user_id': user_id,
            'model_id': model_id,
            'timestamp': datetime.now().isoformat()
        }

        redis_client.push_to_queue(self.prediction_queue, job_data)

        logger.info(f"Submitted prediction job: {job_id} for URL: {url}")

        return job_id

    def submit_batch_prediction_job(
        self,
        urls: List[str],
        user_id: Optional[int] = None,
        model_id: Optional[str] = None
    ) -> str:
        job_id = str(uuid.uuid4())

        job_data = {
            'job_id': job_id,
            'job_type': 'batch_prediction',
            'urls': urls,
            'user_id': user_id,
            'model_id': model_id,
            'timestamp': datetime.now().isoformat()
        }

        redis_client.push_to_queue(self.prediction_queue, job_data)

        logger.info(
            f"Submitted batch prediction job: {job_id} for {len(urls)} URLs")

        return job_id

    async def get_job_result(self, job_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Poll the Redis result cache for `job_id`.

        Uses `asyncio.sleep`, not `time.sleep` -- this coroutine is awaited
        directly from `async def` FastAPI route handlers (via predict_url_sync/
        predict_urls_sync below, and routers/ml/ml_training_route.py's
        get_training_result). Before this fix it used a blocking `time.sleep`
        poll loop with no `asyncio.to_thread`/`run_in_executor` wrapper,
        meaning every prediction request blocked the ASGI event loop for up
        to `timeout` seconds (30-60s), serializing all concurrent request
        handling in that worker process -- flagged in
        SEMD_BACKEND_CURRENT_STATE.md section 8 and fixed here (Domain 12).
        """
        cache_key = f"{self.result_cache_prefix}{job_id}"

        result = redis_client.get_cache(cache_key)
        if result:
            logger.info(f"Found cached result for job: {job_id}")
            return result

        start_time = time.time()
        poll_interval = 0.5

        while time.time() - start_time < timeout:
            result = redis_client.get_cache(cache_key)
            if result:
                logger.info(f"Found result for job: {job_id}")
                return result
            await asyncio.sleep(poll_interval)

        logger.warning(f"Timeout waiting for job result: {job_id}")
        return None

    async def predict_url_sync(
        self,
        url: str,
        user_id: Optional[int] = None,
        model_id: Optional[str] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        # Name kept (not renamed to predict_url_async) to avoid an
        # unnecessary rename across every call site and test mock -- "sync"
        # here describes the request/response contract (caller gets a
        # completed result, not a job handle), not the execution model.
        job_id = self.submit_prediction_job(url, user_id, model_id)

        result = await self.get_job_result(job_id, timeout)

        if result is None:
            return {
                'job_id': job_id,
                'status': 'timeout',
                'error': f"ML service did not respond within {timeout} seconds",
                'url': url
            }

        return result

    async def predict_urls_sync(
        self,
        urls: List[str],
        user_id: Optional[int] = None,
        model_id: Optional[str] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        job_id = self.submit_batch_prediction_job(urls, user_id, model_id)

        result = await self.get_job_result(job_id, timeout)

        if result is None:
            return {
                'job_id': job_id,
                'status': 'timeout',
                'error': f"ML service did not respond within {timeout} seconds",
                'urls': urls
            }

        return result

    def trigger_model_retraining(
        self,
        service_conf_id: int,
        dataset_files: List[str]
    ) -> str:
        logger.info(
            f"Triggering model retraining for service_conf_id: {service_conf_id}")

        job_id = self.submit_training_job(
            service_conf_id=service_conf_id,
            dataset_files=dataset_files,
            run_name=f"retrain_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        return job_id


ml_service_client = MLServiceClient()
