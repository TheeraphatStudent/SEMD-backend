"""Redis worker for processing ML prediction results. This worker listens to
ml_result_queue and caches results for the API to retrieve.

Flow:
1. Backend API sends prediction request to ml_prediction_queue
2. ML Service processes and sends result to ml_result_queue
3. This worker caches the result with key: ml_result:{job_id}
4. Backend API polls the cache to get the result

"""

from services.redis_client import redis_client
import sys
import os
import time
import json
import signal
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLResultWorker:

    def __init__(self):
        self.running = True
        self.result_queue = 'ml_result_queue'
        self.cache_prefix = 'ml_result:'
        self.cache_ttl = 3600

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def process_result(self, result_data: dict) -> bool:
        try:
            job_id = result_data.get('job_id')
            job_type = result_data.get('job_type', 'unknown')
            status = result_data.get('status', 'unknown')

            if not job_id:
                logger.warning('Received result without job_id, skipping')
                return False

            logger.info(
                f"Processing {job_type} result: {job_id} (status: {status})")

            cache_key = f"{self.cache_prefix}{job_id}"
            redis_client.set_cache(cache_key, result_data, ttl=self.cache_ttl)

            logger.info(f"Cached result at: {cache_key}")

            if result_data.get('url'):
                logger.info(f"  URL: {result_data['url']}")
            if result_data.get('prediction'):
                pred = result_data['prediction']
                logger.info(
                    f"  Class: {pred.get('class')}, Confidence: {pred.get('confidence')}")

            return True

        except Exception as e:
            logger.error(f"Error processing result: {e}")
            return False

    def start(self, poll_timeout: int = 5):
        logger.info('=' * 60)
        logger.info('ML Result Worker Started')
        logger.info('=' * 60)
        logger.info(f"Listening to queue: {self.result_queue}")
        logger.info(f"Cache prefix: {self.cache_prefix}")
        logger.info(f"Cache TTL: {self.cache_ttl}s")
        logger.info('Press Ctrl+C to stop')
        logger.info('')

        while self.running:
            try:
                result_data = redis_client.pop_from_queue(
                    self.result_queue,
                    timeout=poll_timeout
                )

                if result_data:
                    self.process_result(result_data)

            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(1)

        logger.info('Worker stopped')


def main():
    worker = MLResultWorker()
    worker.start()


if __name__ == '__main__':
    main()
