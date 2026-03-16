"""Redis worker for processing prediction queue.

This worker listens to the prediction_queue and processes predictions.

"""

from db.mongo_client import get_db
from db.redis_client import pop_from_queue, set_cache
import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def process_prediction(prediction_data: dict):
    """Process prediction from queue.

    Args:
        prediction_data: Prediction data from queue

    """
    try:
        print(f"\n{'='*60}")
        print('Processing prediction from queue...')
        print(f"{'='*60}")

        prediction_id = prediction_data.get('prediction_id')
        url = prediction_data.get('url')
        result = prediction_data.get('result')
        timestamp = prediction_data.get('timestamp')

        print(f"Prediction ID: {prediction_id}")
        print(f"URL: {url}")
        print(f"Result: {json.dumps(result, indent=2)}")
        print(f"Timestamp: {timestamp}")

        print('\n[Worker] Processing prediction...')
        time.sleep(1)

        cache_data = {
            **prediction_data,
            'status': 'processed',
            'processed_at': time.time(),
            'worker_message': 'Prediction processed successfully by worker',
        }
        set_cache(f"prediction:{prediction_id}:processed", cache_data)

        print('[Worker] ✓ Prediction processed successfully!')
        print(
            f"[Worker] Cached result at: prediction:{prediction_id}:processed")
        print(f"{'='*60}\n")

        return True

    except Exception as e:
        print(f"[Worker] ✗ Error processing prediction: {e}")
        return False


def start_worker(queue_name: str = 'prediction_queue', poll_interval: int = 2):
    """Start the Redis worker.

    Args:
        queue_name: Name of the queue to listen to
        poll_interval: Interval in seconds to poll the queue

    """
    print(f"\n{'='*60}")
    print('Redis Prediction Worker Started')
    print(f"{'='*60}")
    print(f"Listening to queue: {queue_name}")
    print(f"Poll interval: {poll_interval} seconds")
    print('Press Ctrl+C to stop\n')

    try:
        while True:
            prediction_data = pop_from_queue(queue_name)

            if prediction_data:
                process_prediction(prediction_data)
            else:
                print(f"[Worker] Queue empty, waiting {poll_interval}s...")
                time.sleep(poll_interval)

    except KeyboardInterrupt:
        print('\n[Worker] Shutting down...')
        print('Worker stopped.')
    except Exception as e:
        print(f"[Worker] Fatal error: {e}")
        raise


if __name__ == '__main__':
    start_worker()
