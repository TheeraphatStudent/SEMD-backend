from sqlalchemy.orm import Session
from typing import List, Dict, Any

from database import User, AccessKey
from models.access_key_request import (
    AccessKeyCreateRequest,
    AccessKeyAdminCreateRequest, AccessKeyAdminUpdateRequest
)
from models.access_key_model import AccessKeyModel
from services.access_key_service import AccessKeyService
from libs.pagination import PaginationParams, PaginationMeta, create_pagination_meta


class AccessKeyControl:
    
    @classmethod
    def create_key(cls, user: User, request: AccessKeyCreateRequest, db: Session) -> Dict[str, Any]:
        key, raw_key = AccessKeyService.create_key(user, request, db)
        key_model = AccessKeyModel.model_validate(key)
        return {
            "key": key_model.model_dump(),
            "access_key": raw_key
        }
    
    @classmethod
    def reset_key(cls, user: User, key_id: int, db: Session) -> Dict[str, Any]:
        key, raw_key = AccessKeyService.reset_key(user, key_id, db)
        key_model = AccessKeyModel.model_validate(key)
        return {
            "key": key_model.model_dump(),
            "access_key": raw_key
        }
    
    @classmethod
    def get_user_keys(cls, user: User, pagination: PaginationParams, db: Session) -> tuple[List[Dict], PaginationMeta]:
        total = AccessKeyService.count_user_keys(user, db)
        keys = AccessKeyService.get_user_keys(user, db, pagination.offset, pagination.limit)
        
        key_list = []
        for key in keys:
            key_data = AccessKeyModel.model_validate(key).model_dump()
            key_data['current_usage'] = AccessKeyService.get_key_current_usage(key.access_key_id, db)
            key_list.append(key_data)
            
        meta = create_pagination_meta(pagination.page, pagination.page_size, total)
        return key_list, meta
    
    @classmethod
    def get_key_usage_monthly(cls, user: User, key_id: int, year: int, month: int, db: Session) -> Dict[str, Any]:
        key = AccessKeyService.get_key_by_id(key_id, db)
        
        if key.user_id != user.user_id:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this key's usage"
            )
        
        return AccessKeyService.get_key_usage_monthly(key_id, year, month, db)
    
    @classmethod
    def get_key_usage_yearly(cls, user: User, key_id: int, year: int, db: Session) -> Dict[str, Any]:
        key = AccessKeyService.get_key_by_id(key_id, db)
        
        if key.user_id != user.user_id:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this key's usage"
            )
        
        return AccessKeyService.get_key_usage_yearly(key_id, year, db)
    
    @classmethod
    def get_key_usage_all_time(cls, user: User, key_id: int, db: Session) -> Dict[str, Any]:
        key = AccessKeyService.get_key_by_id(key_id, db)
        
        if key.user_id != user.user_id:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this key's usage"
            )
        
        return AccessKeyService.get_key_usage_all_time(key_id, db)
    
    @classmethod
    def admin_create_key(cls, request: AccessKeyAdminCreateRequest, db: Session) -> Dict[str, Any]:
        key, raw_key = AccessKeyService.admin_create_key(request, db)
        key_model = AccessKeyModel.model_validate(key)
        return {
            "key": key_model.model_dump(),
            "access_key": raw_key
        }
    
    @classmethod
    def admin_update_key(cls, key_id: int, request: AccessKeyAdminUpdateRequest, db: Session) -> Dict[str, Any]:
        key = AccessKeyService.admin_update_key(key_id, request, db)
        key_model = AccessKeyModel.model_validate(key)
        key_data = key_model.model_dump()
        key_data['current_usage'] = AccessKeyService.get_key_current_usage(key_id, db)
        return key_data
    
    @classmethod
    def admin_delete_key(cls, key_id: int, db: Session) -> bool:
        return AccessKeyService.admin_delete_key(key_id, db)
    
    @classmethod
    def admin_get_all_keys(cls, pagination: PaginationParams, db: Session) -> tuple[List[Dict], PaginationMeta]:
        total = AccessKeyService.count_all_keys(db)
        keys = AccessKeyService.get_all_keys(db, pagination.offset, pagination.limit)
        
        key_list = []
        for key in keys:
            key_data = AccessKeyModel.model_validate(key).model_dump()
            key_data['current_usage'] = AccessKeyService.get_key_current_usage(key.access_key_id, db)
            key_list.append(key_data)
        
        meta = create_pagination_meta(pagination.page, pagination.page_size, total)
        return key_list, meta
    
    @classmethod
    def admin_get_key_usage_monthly(cls, key_id: int, year: int, month: int, db: Session) -> Dict[str, Any]:
        AccessKeyService.get_key_by_id(key_id, db)
        return AccessKeyService.get_key_usage_monthly(key_id, year, month, db)
    
    @classmethod
    def admin_get_key_usage_yearly(cls, key_id: int, year: int, db: Session) -> Dict[str, Any]:
        AccessKeyService.get_key_by_id(key_id, db)
        return AccessKeyService.get_key_usage_yearly(key_id, year, db)
    
    @classmethod
    def admin_get_key_usage_all_time(cls, key_id: int, db: Session) -> Dict[str, Any]:
        AccessKeyService.get_key_by_id(key_id, db)
        return AccessKeyService.get_key_usage_all_time(key_id, db)


access_key_control = AccessKeyControl()
