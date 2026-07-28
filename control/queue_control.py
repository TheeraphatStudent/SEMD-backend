from typing import List, Dict, Any

from models.access.queue_model import QueueItemResponse
from services.queue_service import QueueService


class QueueControl:

    @classmethod
    def get_retrain_queue(cls) -> Dict[str, Any]:
        items = QueueService.get_retrain_queue()
        count = QueueService.get_queue_count()

        return {
            'total': count,
            'items': [item.model_dump() for item in items]
        }

    @classmethod
    def get_queue_count(cls) -> int:
        return QueueService.get_queue_count()


queue_control = QueueControl()
