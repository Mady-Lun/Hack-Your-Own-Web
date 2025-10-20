# Import all models to ensure they are registered with SQLAlchemy
from app.models.user import User, RefreshToken
from app.models.scan import Scan, ScanAlert, ScanStatus, ScanType, RiskLevel

__all__ = [
    "User",
    "RefreshToken",
    "Scan",
    "ScanAlert",
    "ScanStatus",
    "ScanType",
    "RiskLevel",
]
