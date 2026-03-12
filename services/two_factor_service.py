import pyotp
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from database import User

class TwoFactorService:
    
    def __init__(self):
        pass
    
    @classmethod
    def generate_totp_secret(cls) -> str:
        return pyotp.random_base32()
    
    @classmethod
    def get_totp_uri(cls, secret: str, email: str) -> str:
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name="SEMD")
    
    @classmethod
    def verify_totp(cls, secret: str, code: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    
    @classmethod
    def enable_2fa(cls, user: User, secret: str, db: Session):
        user.twofa_secret = secret
        user.is_2fa_enabled = True
        db.commit()
        db.refresh(user)

two_factor_service = TwoFactorService()
