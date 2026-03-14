from sqlalchemy.orm import Session
from typing import List, Optional

from services.service_conf_service import ServiceConfService
from database import ServiceConf

class ServiceConfControl:
    def __init__(self, db: Session, user_id: int):
        self.service = ServiceConfService(db)
        self.user_id = user_id
    
    def list_services(self, service_type: Optional[str] = None) -> List[ServiceConf]:
        return self.service.get_user_services(self.user_id)
    
    def get_service(self, service_id: int) -> ServiceConf:
        return self.service.get_service_by_id(service_id, self.user_id)
    
    def activate_service(self, service_id: int) -> ServiceConf:
        return self.service.toggle_service_active(service_id, self.user_id, True)
    
    def deactivate_service(self, service_id: int) -> ServiceConf:
        return self.service.toggle_service_active(service_id, self.user_id, False)
    
    def get_active_services(self, service_type: Optional[str] = None) -> List[ServiceConf]:
        return self.service.get_active_services(self.user_id, service_type)
