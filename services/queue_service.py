from datetime import datetime
from typing import List, Optional
import json

from services.client.redis_client import redis_client
from models.queue_model import QueueItem, PredictByInfo, QueueItemResponse
from database import User


RETRAIN_QUEUE_KEY = 'retrain_url_queue'


class QueueService:

    @classmethod
    def add_to_retrain_queue(cls, url: str, user: Optional[User] = None) -> bool:
        predict_by = PredictByInfo(
            user_id=user.user_id if user else None,
            profile_img_url=user.profile_img_uri if user else None,
            username=user.username if user else None
        )

        queue_item = QueueItem(
            url=url,
            created_at=datetime.utcnow(),
            predict_by=predict_by
        )

        data = {
            'url': queue_item.url,
            'created_at': queue_item.created_at.isoformat(),
            'predict_by': {
                'user_id': predict_by.user_id,
                'profile_img_url': predict_by.profile_img_url,
                'username': predict_by.username
            }
        }

        redis_client.push_to_queue(RETRAIN_QUEUE_KEY, data)
        return True

    @classmethod
    def get_retrain_queue(cls) -> List[QueueItemResponse]:
        queue_data = redis_client.client.lrange(RETRAIN_QUEUE_KEY, 0, -1)

        items = []
        for item_str in queue_data:
            item_data = json.loads(item_str)
            items.append(QueueItemResponse(
                url=item_data['url'],
                created_at=item_data['created_at'],
                predict_by=PredictByInfo(
                    user_id=item_data['predict_by'].get('user_id'),
                    profile_img_url=item_data['predict_by'].get(
                        'profile_img_url'),
                    username=item_data['predict_by'].get('username')
                )
            ))

        return items

    @classmethod
    def get_queue_count(cls) -> int:
        return redis_client.client.llen(RETRAIN_QUEUE_KEY)

    @classmethod
    def clear_queue(cls) -> bool:
        redis_client.client.delete(RETRAIN_QUEUE_KEY)
        return True


queue_service = QueueService()
