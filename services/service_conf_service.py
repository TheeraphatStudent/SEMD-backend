from sqlalchemy.orm import Session
from sqlalchemy import select, update
from fastapi import HTTPException, status
from datetime import datetime
from typing import List, Optional

from database import ServiceConf, ThirdServiceConf, ModelRegistry
from libs.types.enums import ServiceType

class ServiceConfService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_services(self, user_id: int) -> List[ServiceConf]:
        services = self.db.query(ServiceConf).filter(
            ServiceConf.user_id == user_id
        ).all()
        return services
    
    def get_service_by_id(self, service_id: int, user_id: int = None) -> ServiceConf:
        query = self.db.query(ServiceConf).filter(ServiceConf.service_conf_id == service_id)
        
        if user_id:
            query = query.filter(ServiceConf.user_id == user_id)
        
        service = query.first()
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service configuration not found"
            )
        
        return service
    
    def toggle_service_active(self, service_id: int, user_id: int, is_active: bool) -> ServiceConf:
        service = self.get_service_by_id(service_id, user_id)
        
        service.is_active = is_active
        service.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(service)
        
        return service
    
    def get_active_services(self, user_id: int = None, service_type: Optional[str] = None) -> List[ServiceConf]:
        query = self.db.query(ServiceConf).filter(ServiceConf.is_active == True)
        
        if user_id:
            query = query.filter(ServiceConf.user_id == user_id)
        
        if service_type:
            query = query.filter(ServiceConf.service_type == service_type)
        
        return query.all()
