"""Compliance and jurisdiction models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer, Float,
    ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base


class Jurisdiction(Base):
    """Jurisdiction definitions and requirements."""

    __tablename__ = "jurisdictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    region = Column(String(100), nullable=True)
    legal_system = Column(String(50), nullable=False)  # common_law, civil_law, hybrid

    # Requirements
    mandatory_clauses = Column(JSON, default=list)
    prohibited_clauses = Column(JSON, default=list)
    language_requirements = Column(ARRAY(String), default=list)
    filing_requirements = Column(JSON, default=dict)
    governing_statutes = Column(JSON, default=list)

    # Special Requirements
    data_protection_law = Column(String(100), nullable=True)  # GDPR, CCPA, etc.
    consumer_protection = Column(JSON, default=dict)
    employment_law_specifics = Column(JSON, default=dict)
    tax_implications = Column(JSON, default=dict)

    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Jurisdiction(code={self.code}, name={self.name})>"


class ComplianceRule(Base):
    """Compliance rules and regulatory requirements."""

    __tablename__ = "compliance_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_code = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)

    # Classification
    category = Column(String(100), nullable=False, index=True)  # GDPR, HIPAA, SOX, etc.
    subcategory = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    jurisdictions = Column(ARRAY(String), default=list)
    contract_types = Column(ARRAY(String), default=list)

    # Rule Logic
    rule_type = Column(String(50), nullable=False)  # mandatory_inclusion, prohibited, conditional
    rule_logic = Column(JSON, nullable=False)  # Machine-readable rule definition
    validation_pattern = Column(Text, nullable=True)  # Regex or pattern for validation
    required_keywords = Column(ARRAY(String), default=list)
    prohibited_keywords = Column(ARRAY(String), default=list)

    # Legal Reference
    statute_reference = Column(String(500), nullable=True)
    regulation_url = Column(String(500), nullable=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    sunset_date = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")
    last_reviewed = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<ComplianceRule(code={self.rule_code}, category={self.category})>"


class ComplianceCheck(Base):
    """Compliance check results for contracts."""

    __tablename__ = "compliance_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    jurisdiction = Column(String(50), nullable=False)
    checked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Results
    overall_status = Column(String(20), nullable=False)  # compliant, non_compliant, partial, pending
    compliance_score = Column(Float, default=0.0)
    total_rules_checked = Column(Integer, default=0)
    rules_passed = Column(Integer, default=0)
    rules_failed = Column(Integer, default=0)
    rules_warning = Column(Integer, default=0)

    # Detailed Results
    results = Column(JSON, default=list)  # Array of ComplianceResult
    recommendations = Column(JSON, default=list)
    required_actions = Column(JSON, default=list)

    # Metadata
    check_duration_ms = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    contract = relationship("Contract", back_populates="compliance_checks")

    def __repr__(self):
        return f"<ComplianceCheck(contract={self.contract_id}, status={self.overall_status})>"


class ComplianceResult(Base):
    """Individual compliance rule check results."""

    __tablename__ = "compliance_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    check_id = Column(UUID(as_uuid=True), ForeignKey("compliance_checks.id", ondelete="CASCADE"), nullable=False)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("compliance_rules.id"), nullable=False)

    status = Column(String(20), nullable=False)  # passed, failed, warning, not_applicable
    confidence = Column(Float, default=0.0)
    explanation = Column(Text, nullable=True)
    affected_clauses = Column(JSON, default=list)
    remediation = Column(Text, nullable=True)
    severity = Column(String(20), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RegulatoryUpdate(Base):
    """Track regulatory changes affecting contracts."""

    __tablename__ = "regulatory_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    jurisdiction = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    impact_level = Column(String(20), nullable=False)  # critical, high, medium, low

    # Change Details
    effective_date = Column(DateTime(timezone=True), nullable=False)
    source_url = Column(String(500), nullable=True)
    affected_contract_types = Column(ARRAY(String), default=list)
    affected_clauses = Column(ARRAY(String), default=list)
    required_changes = Column(JSON, default=list)

    # Processing
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    contracts_affected_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
