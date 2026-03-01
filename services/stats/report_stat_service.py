from typing import List, Dict, Any
from datetime import datetime, timedelta

class ReportStatService:
    
    @staticmethod
    async def get_report_statistics() -> Dict[str, int]:
        return {
            "reported_by_amount": 0,
            "safe_urls": 0,
            "malicious_urls": 0,
            "error_urls": 0,
            "pending_urls": 0
        }
    
    @staticmethod
    async def get_report_list(limit: int = 10) -> List[Dict[str, Any]]:
        return []
    
    @staticmethod
    async def get_report_trend(days: int = 30) -> List[Dict[str, Any]]:
        return []
    
    @staticmethod
    async def get_report_details(status: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        return []
