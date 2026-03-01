import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from services.client import redis_client
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLServiceClient:
    
    def __init__(self):
        self.training_queue = "ml_training_queue"
        self.prediction_queue = "ml_prediction_queue"
        self.result_queue = "ml_result_queue"
    
    def submit_training_job(
        self,
        service_conf_id: int,
        dataset_files: List[str],
        algorithms: Optional[List[str]] = None,
        run_name: Optional[str] = None
    ) -> str:
        job_id = str(uuid.uuid4())
        
        if algorithms is None:
            algorithms = ["svm", "xgboost", "random_forest"]
        
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
        
        logger.info(f"Submitted batch prediction job: {job_id} for {len(urls)} URLs")
        
        return job_id
    
    def get_job_result(self, job_id: str, timeout: int = 300) -> Optional[Dict[str, Any]]:
        cache_key = f"ml_result:{job_id}"
        
        result = redis_client.get_cache(cache_key)
        if result:
            return result
        
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result_data = redis_client.pop_from_queue(self.result_queue, timeout=5)
            
            if result_data and result_data.get('job_id') == job_id:
                redis_client.set_cache(cache_key, result_data, ttl=3600)
                return result_data
            
            if result_data:
                other_cache_key = f"ml_result:{result_data.get('job_id')}"
                redis_client.set_cache(other_cache_key, result_data, ttl=3600)
        
        return None
    
    def trigger_model_retraining(
        self,
        service_conf_id: int,
        dataset_files: List[str]
    ) -> str:
        logger.info(f"Triggering model retraining for service_conf_id: {service_conf_id}")
        
        job_id = self.submit_training_job(
            service_conf_id=service_conf_id,
            dataset_files=dataset_files,
            run_name=f"retrain_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        return job_id


ml_service_client = MLServiceClient()
