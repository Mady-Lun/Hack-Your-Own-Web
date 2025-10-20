from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from app.models.user import User


class ScanStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanType(str, Enum):
    BASIC = "basic"           # Basic passive scan (spider + passive) - No verification required
    FULL = "full"             # Full active scan - Requires domain ownership verification


class Scan(SQLModel, table=True):
    __tablename__ = "scans" # type: ignore

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False, index=True)
    target_url: str = Field(nullable=False, index=True)
    scan_type: ScanType = Field(
        default=ScanType.BASIC,
        sa_column=Column(PgEnum(ScanType, name="scantype", create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False)
    )
    status: ScanStatus = Field(
        default=ScanStatus.PENDING,
        sa_column=Column(PgEnum(ScanStatus, name="scanstatus", create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    )

    # Celery task tracking
    celery_task_id: Optional[str] = Field(default=None, nullable=True, index=True)

    # Scan configuration
    scan_config: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # Progress tracking
    progress_percentage: int = Field(default=0, nullable=False)
    current_step: Optional[str] = Field(default=None, nullable=True)

    # Results summary
    total_alerts: int = Field(default=0, nullable=False)
    high_risk_count: int = Field(default=0, nullable=False)
    medium_risk_count: int = Field(default=0, nullable=False)
    low_risk_count: int = Field(default=0, nullable=False)
    info_count: int = Field(default=0, nullable=False)

    # Error tracking
    error_message: Optional[str] = Field(default=None, nullable=True)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    started_at: Optional[datetime] = Field(default=None, nullable=True)
    completed_at: Optional[datetime] = Field(default=None, nullable=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    user: "User" = Relationship(back_populates="scans")
    alerts: List["ScanAlert"] = Relationship(
        back_populates="scan",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "passive_deletes": True,
        }
    )


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class ScanAlert(SQLModel, table=True):
    __tablename__ = "scan_alerts" # type: ignore

    id: int = Field(default=None, primary_key=True)
    scan_id: int = Field(foreign_key="scans.id", nullable=False, index=True)

    # Alert details
    alert_name: str = Field(nullable=False, index=True)
    risk_level: RiskLevel = Field(
        sa_column=Column(PgEnum(RiskLevel, name="risklevel", create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    )
    confidence: str = Field(nullable=False)  # High, Medium, Low

    # Vulnerability details
    description: Optional[str] = Field(default=None, nullable=True)
    solution: Optional[str] = Field(default=None, nullable=True)
    reference: Optional[str] = Field(default=None, nullable=True)
    cwe_id: Optional[str] = Field(default=None, nullable=True)
    wasc_id: Optional[str] = Field(default=None, nullable=True)

    # Location
    url: str = Field(nullable=False)
    method: Optional[str] = Field(default=None, nullable=True)
    param: Optional[str] = Field(default=None, nullable=True)
    attack: Optional[str] = Field(default=None, nullable=True)
    evidence: Optional[str] = Field(default=None, nullable=True)

    # Additional data
    other_info: Optional[str] = Field(default=None, nullable=True)
    alert_tags: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    scan: Scan = Relationship(back_populates="alerts")
