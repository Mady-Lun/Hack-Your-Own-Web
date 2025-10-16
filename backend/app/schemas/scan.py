from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.models.scan import ScanStatus, ScanType, RiskLevel


class ScanCreate(BaseModel):
    target_url: HttpUrl = Field(..., description="The target URL to scan")
    scan_type: ScanType = Field(default=ScanType.BASIC, description="Type of scan to perform (basic or full)")
    scan_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional scan configuration options"
    )

    @validator('target_url')
    def validate_url(cls, v):
        url_str = str(v)
        if not url_str.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return url_str

    class Config:
        json_schema_extra = {
            "example": {
                "target_url": "https://example.com",
                "scan_type": "basic",
                "scan_config": {}
            }
        }


class ScanUpdate(BaseModel):
    status: Optional[ScanStatus] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    current_step: Optional[str] = None
    error_message: Optional[str] = None


class ScanAlertResponse(BaseModel):
    id: int
    alert_name: str
    risk_level: RiskLevel
    confidence: str
    description: Optional[str] = None
    solution: Optional[str] = None
    reference: Optional[str] = None
    cwe_id: Optional[str] = None
    wasc_id: Optional[str] = None
    url: str
    method: Optional[str] = None
    param: Optional[str] = None
    attack: Optional[str] = None
    evidence: Optional[str] = None
    other_info: Optional[str] = None
    alert_tags: Optional[Dict[str, Any]] = None
    created_at: datetime


class ScanResponse(BaseModel):
    id: int
    user_id: int
    target_url: str
    scan_type: ScanType
    status: ScanStatus
    celery_task_id: Optional[str] = None
    progress_percentage: int
    current_step: Optional[str] = None
    total_alerts: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    info_count: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime


class ScanDetailResponse(ScanResponse):
    alerts: List[ScanAlertResponse] = []


class ScanListResponse(BaseModel):
    scans: List[ScanResponse]
    total: int
    page: int
    page_size: int


class ScanStatsResponse(BaseModel):
    total_scans: int
    pending_scans: int
    in_progress_scans: int
    completed_scans: int
    failed_scans: int
    total_vulnerabilities: int
    high_risk_vulnerabilities: int
    medium_risk_vulnerabilities: int
    low_risk_vulnerabilities: int
