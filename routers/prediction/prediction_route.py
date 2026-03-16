from routers import BaseRoute
from fastapi import UploadFile, HTTPException
from models import PredictionResponse, PredictionRequest
from typing import Any

# Batch processing
import csv
import io

import pickle
import os

class PredictionRoute(BaseRoute):
    def __init__(self):
        super().__init__(
            prefix="/prediction",
            tags=["prediction"],
            responses={404: {"description": "Not found"}, 501: {"description": "Not implemented"}, 422: {"description": "Validation error"}}
        )

        self.router.post(
            "/predict", 
            response_model=PredictionResponse,
            summary="Predict URL",
            description="Predict if a URL is malicious or not"
        )(self.predict)

    async def predict(self, request: PredictionRequest):
        urls = []
        
        if request.url:
            if isinstance(request.url, str):
                urls = [request.url]
            elif isinstance(request.url, list):
                urls = request.url
        
        if request.text_file:
            content = await request.text_file.read()
            text = content.decode('utf-8')
            file_urls = [line.strip() for line in text.split('\n') if line.strip()]
            urls.extend(file_urls)
        
        if request.csv_file:
            content = await request.csv_file.read()
            text = content.decode('utf-8')
            reader = csv.DictReader(io.StringIO(text))
            for row in reader:
                if 'url' in row and row['url'].strip():
                    urls.append(row['url'].strip())
                elif row:
                    first_value = list(row.values())[0].strip()
                    if first_value:
                        urls.append(first_value)
        
        if not urls:
            raise HTTPException(status_code=422, detail="No URLs provided")

        model_path = os.path.join(os.path.dirname(__file__), "../../../SEMD-ml/models/xgboost_model_8bdc3ff795714d1a8ef57120a9a9ad1f.pkl")
        
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail=f"Model file not found: {model_path}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading model: {str(e)}")

        results = []
        for url in urls:
            try:
                result = model.predict([url])[0]
                is_malicious = bool(result)
                confidence = 0.95 if not is_malicious else 0.87
                results.append({
                    "url": url,
                    "is_malicious": is_malicious,
                    "confidence": confidence
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "error": f"Prediction error: {str(e)}"
                })

        return PredictionResponse(data=results)
