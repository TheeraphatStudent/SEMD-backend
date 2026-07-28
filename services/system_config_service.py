from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.db import SystemConfig
from models.service.system_config_model import SystemConfigUpdateRequest


class SystemConfigService:

    @classmethod
    def get_all_configs(cls, db: Session) -> list[SystemConfig]:
        return db.query(SystemConfig).order_by(SystemConfig.config_key).all()

    @classmethod
    def get_config_by_key(cls, config_key: str, db: Session) -> SystemConfig:
        config = db.query(SystemConfig).filter(
            SystemConfig.config_key == config_key).first()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Config with key '{config_key}' not found"
            )
        return config

    @classmethod
    def get_config_by_id(cls, config_id: int, db: Session) -> SystemConfig:
        config = db.query(SystemConfig).filter(
            SystemConfig.system_config_id == config_id).first()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Config with id {config_id} not found"
            )
        return config

    @classmethod
    def update_config_by_key(cls, config_key: str, request: SystemConfigUpdateRequest, db: Session) -> SystemConfig:
        config = cls.get_config_by_key(config_key, db)

        config.config_value = request.config_value
        if request.description is not None:
            config.description = request.description
        config.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(config)

        return config

    @classmethod
    def update_config_by_id(cls, config_id: int, request: SystemConfigUpdateRequest, db: Session) -> SystemConfig:
        config = cls.get_config_by_id(config_id, db)

        config.config_value = request.config_value
        if request.description is not None:
            config.description = request.description
        config.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(config)

        return config


system_config_service = SystemConfigService()
