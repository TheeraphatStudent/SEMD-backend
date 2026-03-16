from sqlalchemy.orm import Session

from models.system_config_model import SystemConfigModel, SystemConfigUpdateRequest
from services.system_config_service import SystemConfigService


class SystemConfigControl:

    @classmethod
    def get_all_configs(cls, db: Session) -> list[SystemConfigModel]:
        configs = SystemConfigService.get_all_configs(db)
        return [SystemConfigModel.model_validate(config) for config in configs]

    @classmethod
    def get_config_by_key(cls, config_key: str, db: Session) -> SystemConfigModel:
        config = SystemConfigService.get_config_by_key(config_key, db)
        return SystemConfigModel.model_validate(config)

    @classmethod
    def update_config_by_key(cls, config_key: str, request: SystemConfigUpdateRequest, db: Session) -> SystemConfigModel:
        config = SystemConfigService.update_config_by_key(
            config_key, request, db)
        return SystemConfigModel.model_validate(config)


system_config_control = SystemConfigControl()
