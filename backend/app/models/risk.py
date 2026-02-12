"""Risk assessment models."""

import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, DateTime, Enum, Text, Integer, Float,
    ForeignKey, JSON, Boolean
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base


class RiskCategory(str, enum.Enum):
    """Categories of legal risk."""
    FINANCIAL = "financial"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    REPUTATIONAL = "reputational"
    LEGAL_LIABILITY = "legal_liability"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    DATA_PRIVACY = "data_privacy"
    CONTRACTUAL = "contractual"
    JURISDICTIONAL = "jurisdictional"
    FORCE_MAJEURE = "force_majeure"
    TERMINATION = "termination"
    INDEMNIFICATION = "indemnification"
    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    CONFIDENTIALITY = "confidentiality"
    NON_COMPETE = "non_compete"
    DISPUTE_RESOLUTION = "dispute_resolution"


class RiskAssessment(Base):
    """Overall risk assessment for a contract."""

    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Overall Scores
    overall_risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    confidence_score = Column(Float, default=0.0)

    # Category Breakdown
    category_scores = Column(JSON, default=dict)  # {category: score}
    risk_distribution = Column(JSON, default=dict)  # Statistical distribution

    # Analysis Details
    total_factors_analyzed = Column(Integer, default=0)
    high_risk_factors = Column(Integer, default=0)
    medium_risk_factors = Column(Integer, default=0)
    low_risk_factors = Column(Integer, default=0)

    # AI Explanation
    executive_summary = Column(Text, nullable=True)
    key_findings = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)
    mitigations = Column(JSON, default=list)

    # Comparison
    industry_benchmark = Column(Float, nullable=True)
    similar_contracts_avg = Column(Float, nullable=True)
    percentile_rank = Column(Float, nullable=True)

    # Metadata
    model_used = Column(String(100), nullable=True)
    analysis_duration_ms = Column(Integer, nullable=True)
    precedents_analyzed = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    contract = relationship("Contract", back_populates="risk_assessments")
    risk_factors = relationship("RiskScore", back_populates="assessment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<RiskAssessment(contract={self.contract_id}, score={self.overall_risk_score})>"


class RiskFactor(Base):
    """Catalog of risk factors analyzed during review."""

    __tablename__ = "risk_factors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    factor_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(RiskCategory), nullable=False, index=True)

    # Risk Parameters
    default_weight = Column(Float, default=1.0)
    severity_level = Column(String(20), nullable=False)  # low, medium, high, critical
    contract_types = Column(ARRAY(String), default=list)
    jurisdictions = Column(ARRAY(String), default=list)

    # Detection
    detection_keywords = Column(ARRAY(String), default=list)
    detection_patterns = Column(JSON, default=list)  # Regex patterns
    absence_risk = Column(Boolean, default=False)  # Risk if clause is MISSING

    # Context
    legal_basis = Column(Text, nullable=True)
    typical_range = Column(JSON, nullable=True)  # Expected values/ranges
    industry_specific = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<RiskFactor(code={self.factor_code}, category={self.category})>"


class RiskScore(Base):
    """Individual risk factor scores for an assessment."""

    __tablename__ = "risk_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("risk_assessments.id", ondelete="CASCADE"), nullable=False)
    factor_id = Column(UUID(as_uuid=True), ForeignKey("risk_factors.id"), nullable=False)

    # Score
    score = Column(Float, nullable=False)
    weight = Column(Float, default=1.0)
    weighted_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)

    # Explainability
    explanation = Column(Text, nullable=False)
    evidence = Column(JSON, default=list)  # Text snippets from contract
    affected_clauses = Column(JSON, default=list)
    legal_precedents = Column(JSON, default=list)
    suggested_remediation = Column(Text, nullable=True)

    # Comparison
    market_standard = Column(Float, nullable=True)
    deviation_from_standard = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    assessment = relationship("RiskAssessment", back_populates="risk_factors")

    def __repr__(self):
        return f"<RiskScore(factor={self.factor_id}, score={self.score})>"


class DisputeOutcome(Base):
    """Historical dispute outcomes for predictive analysis."""

    __tablename__ = "dispute_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_reference = Column(String(255), nullable=False, index=True)
    jurisdiction = Column(String(50), nullable=False)
    contract_type = Column(String(50), nullable=False)

    # Dispute Details
    dispute_category = Column(String(100), nullable=False)
    disputed_clauses = Column(JSON, default=list)
    issues = Column(JSON, default=list)

    # Outcome
    outcome = Column(String(50), nullable=False)  # plaintiff_won, defendant_won, settled, dismissed
    damages_awarded = Column(Float, nullable=True)
    key_factors = Column(JSON, default=list)
    ruling_summary = Column(Text, nullable=True)
    precedent_value = Column(Float, default=0.0)

    # Metadata
    court = Column(String(255), nullable=True)
    judge = Column(String(255), nullable=True)
    decision_date = Column(DateTime(timezone=True), nullable=True)
    source_url = Column(String(500), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
