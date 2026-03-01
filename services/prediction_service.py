"""
Prediction service - Business logic for URL prediction.
"""

from mimetypes import init
import uuid
from datetime import datetime

from service.postgres_client import postgres_client
from service.redis_client import redis_client
from models.predic import PredictionResult

class PredictionService:
    
    def __init__(self) -> None:
        pass
    
    @classmethod
    def generate_mock_prediction(self, url: str) -> dict:
        """Generate mock prediction result."""
        is_malicious = "true" if "google" in url.lower() else "false"
        accuracy = 0.95 if is_malicious == "true" else 0.87
        suggested = "safe" if is_malicious == "true" else "block"

        return {
            "is_malicious": is_malicious,
            "accurate": accuracy,
            "suggested": suggested,
        }

    @classmethod
    def predict_url(self, url: str) -> dict:
        return self.predict_url_mock(url=url)

    @classmethod
    def predict_url_mock(self, url: str) -> dict:
        """
        Predict if a URL is malicious.
        
        Args:
            url: URL to analyze
            
        Returns:
            dict: Prediction result with ID
        """
        try:
            # Generate mock prediction
            prediction_result = self.generate_mock_prediction(url)
            
            # Generate unique ID
            prediction_id = str(uuid.uuid4())
            
            # Save to PostgreSQL
            with postgres_client.get_session() as session:
                db_prediction = PredictionResult(
                    id=prediction_id,
                    predicted_by_id="model_001",
                    predicted_by_type="ml_model",
                    user_id="user_001",
                    user_type="api_user",
                    from_service="prediction_api",
                    url=url,
                    is_malicious=prediction_result["is_malicious"],
                    accuracy=prediction_result["accurate"],
                    suggested=prediction_result["suggested"],
                )
                session.add(db_prediction)
            
            # Prepare Redis data
            redis_data = {
                "prediction_id": prediction_id,
                "url": url,
                "result": prediction_result,
            }
            
            # Push to queue for async processing
            redis_client.push_to_queue("prediction_queue", redis_data)
            
            # Cache the result
            redis_client.set_cache(f"prediction:{prediction_id}", redis_data)
            
            return {
                "id": prediction_id,
                "url": url,
                "result": prediction_result,
            }
            
        except Exception as e:
            raise Exception(f"Prediction failed: {str(e)}")

    @classmethod
    def get_prediction(self, prediction_id: str) -> dict:
        return self.get_prediction_mock(prediction_id=prediction_id)

    @classmethod
    def get_prediction_mock(self, prediction_id: str) -> dict:
        """
        Get prediction result by ID from cache or PostgreSQL.
        
        Args:
            prediction_id: ID of the prediction
            
        Returns:
            dict: Prediction result with source (cache or database)
            
        Raises:
            Exception: If prediction not found
        """
        try:
            # Check cache first
            cached = redis_client.get_cache(f"prediction:{prediction_id}")
            if cached:
                return {"source": "cache", "data": cached}
            
            # Query PostgreSQL
            with postgres_client.get_session() as session:
                result = session.query(PredictionResult).filter(
                    PredictionResult.id == prediction_id
                ).first()
                
                if not result:
                    raise Exception("Prediction not found")
                
                data = {
                    "id": result.id,
                    "url": result.url,
                    "result": {
                        "is_malicious": result.is_malicious,
                        "accurate": result.accuracy,
                        "suggested": result.suggested,
                    },
                    "predicted_by": {
                        "predicted_id": result.predicted_by_id,
                        "type": result.predicted_by_type,
                    },
                    "usage_by": {
                        "user_id": result.user_id,
                        "type": result.user_type,
                    },
                    "from_service": result.from_service,
                    "created_at": result.created_at.isoformat() if result.created_at else None,
                    "updated_at": result.updated_at.isoformat() if result.updated_at else None,
                }
            
            return {"source": "database", "data": data}
            
        except Exception as e:
            raise Exception(f"Failed to retrieve prediction: {str(e)}")

prediction_service = PredictionService()
