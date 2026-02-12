"""Audit trail models for regulatory compliance."""

import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class AuditAction(str, enum.Enum):
    """Auditable actions in the system."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLED = "mfa_enabled"

    # Contract Operations
    CONTRACT_CREATED = "contract_created"
    CONTRACT_VIEWED = "contract_viewed"
    CONTRACT_UPDATED = "contract_updated"
    CONTRACT_DELETED = "contract_deleted"
    CONTRACT_GENERATED = "contract_generated"
    CONTRACT_EXPORTED = "contract_exported"
    CONTRACT_SIGNED = "contract_signed"

    # Review Operations
    REVIEW_STARTED = "review_started"
    REVIEW_COMPLETED = "review_completed"
    RISK_ASSESSED = "risk_assessed"
    COMPLIANCE_CHECKED = "compliance_checked"

    # Version Control
    VERSION_CREATED = "version_created"
    VERSION_RESTORED = "version_restored"
    BRANCH_CREATED = "branch_created"
    BRANCH_MERGED = "branch_merged"

    # Administrative
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DEACTIVATED = "user_deactivated"
    PERMISSION_CHANGED = "permission_changed"
    TEMPLATE_CREATED = "template_created"
    TEMPLATE_UPDATED = "template_updated"

    # Data Access
    DATA_EXPORTED = "data_exported"
    DATA_DECRYPTED = "data_decrypted"
    SENSITIVE_ACCESS = "sensitive_access"


class AuditLog(Base):
    """Comprehensive audit trail for all system actions."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(Enum(AuditAction), nullable=False, index=True)

    # Context
    resource_type = Column(String(100), nullable=True, index=True)  # contract, user, template, etc.
    resource_id = Column(String(255), nullable=True, index=True)
    description = Column(Text, nullable=True)

    # Request Details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)

    # Change Tracking
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    changes_summary = Column(Text, nullable=True)

    # Security Context
    session_id = Column(String(255), nullable=True)
    organization = Column(String(255), nullable=True)
    risk_level = Column(String(20), default="normal")  # normal, elevated, critical

    # Metadata
    metadata_ = Column("metadata", JSON, default=dict)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user={self.user_id})>"
