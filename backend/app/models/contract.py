"""Contract and related models."""

import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, Enum, Text, Integer, 
    Float, ForeignKey, JSON, Table
)
from sqlalchemy.types import Uuid as UUID
from sqlalchemy.types import JSON as ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base


class ContractStatus(str, enum.Enum):
    """Contract lifecycle states."""
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    NEGOTIATION = "negotiation"
    EXECUTED = "executed"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    ARCHIVED = "archived"


class ContractType(str, enum.Enum):
    """Supported contract types."""
    NDA = "nda"
    MSA = "msa"
    EMPLOYMENT = "employment"
    CONSULTING = "consulting"
    LICENSE = "license"
    PARTNERSHIP = "partnership"
    REAL_ESTATE = "real_estate"
    MERGER_ACQUISITION = "merger_acquisition"
    SERVICE_AGREEMENT = "service_agreement"
    PURCHASE_ORDER = "purchase_order"
    LEASE = "lease"
    LOAN = "loan"
    SUPPLY = "supply"
    DISTRIBUTION = "distribution"
    FRANCHISE = "franchise"
    JOINT_VENTURE = "joint_venture"
    SETTLEMENT = "settlement"
    CUSTOM = "custom"


# Many-to-many relationship for contract tags
contract_tags = Table(
    "contract_tags",
    Base.metadata,
    Column("contract_id", UUID(as_uuid=True), ForeignKey("contracts.id")),
    Column("tag", String(100)),
)


class Contract(Base):
    """Main contract model."""

    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    contract_type = Column(Enum(ContractType), nullable=False, index=True)
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT, index=True)

    # Content
    content = Column(Text, nullable=True)  # Full contract text (encrypted at rest)
    content_hash = Column(String(64), nullable=True)  # SHA-256 for integrity
    summary = Column(Text, nullable=True)
    language = Column(String(10), default="en")

    # Contract Details
    jurisdiction = Column(String(50), nullable=False, index=True)
    governing_law = Column(String(100), nullable=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    value = Column(Float, nullable=True)  # Contract monetary value
    currency = Column(String(3), default="USD")

    # AI Metadata
    ai_generated = Column(Boolean, default=False)
    generation_model = Column(String(100), nullable=True)
    generation_prompt = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    compliance_status = Column(String(50), default="pending")

    # Ownership
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)

    # Version Control
    current_version = Column(Integer, default=1)
    is_locked = Column(Boolean, default=False)
    locked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Metadata
    metadata_ = Column("metadata", JSON, default=dict)
    tags = Column(ARRAY(String), default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    created_by_user = relationship("User", back_populates="contracts", foreign_keys=[created_by])
    clauses = relationship("ContractClause", back_populates="contract", cascade="all, delete-orphan")
    parties = relationship("ContractParty", back_populates="contract", cascade="all, delete-orphan")
    versions = relationship("ContractVersion", back_populates="contract", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="contract", cascade="all, delete-orphan")
    compliance_checks = relationship("ComplianceCheck", back_populates="contract", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Contract(id={self.id}, title={self.title}, type={self.contract_type})>"


class ContractClause(Base):
    """Individual clauses within a contract."""

    __tablename__ = "contract_clauses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    clause_number = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    clause_type = Column(String(100), nullable=False)  # indemnification, limitation_of_liability, etc.

    # AI Analysis
    risk_score = Column(Float, default=0.0)
    risk_explanation = Column(Text, nullable=True)
    compliance_flags = Column(JSON, default=list)
    suggested_alternatives = Column(JSON, default=list)
    legal_precedents = Column(JSON, default=list)

    # Metadata
    is_standard = Column(Boolean, default=True)
    is_negotiable = Column(Boolean, default=True)
    position = Column(Integer, default=0)
    source_template_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    contract = relationship("Contract", back_populates="clauses")

    def __repr__(self):
        return f"<ContractClause(id={self.id}, number={self.clause_number}, title={self.title})>"


class ContractTemplate(Base):
    """Contract templates for different types and jurisdictions."""

    __tablename__ = "contract_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    contract_type = Column(Enum(ContractType), nullable=False, index=True)
    jurisdiction = Column(String(50), nullable=False, index=True)
    language = Column(String(10), default="en")

    # Template Content
    template_content = Column(Text, nullable=False)
    variables = Column(JSON, default=list)  # Required template variables
    clause_structure = Column(JSON, default=list)  # Ordered clause types
    default_clauses = Column(JSON, default=dict)

    # Metadata
    version = Column(String(20), default="1.0")
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    industry = Column(String(100), nullable=True)
    complexity_level = Column(String(20), default="standard")  # simple, standard, complex

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<ContractTemplate(id={self.id}, name={self.name}, type={self.contract_type})>"


class ContractParty(Base):
    """Parties involved in a contract."""

    __tablename__ = "contract_parties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    party_role = Column(String(100), nullable=False)  # discloser, recipient, employer, etc.
    entity_name = Column(String(500), nullable=False)
    entity_type = Column(String(50), nullable=False)  # individual, corporation, llc, partnership
    jurisdiction = Column(String(50), nullable=True)
    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    signing_authority = Column(String(255), nullable=True)
    signed = Column(Boolean, default=False)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    contract = relationship("Contract", back_populates="parties")


class ClauseLibrary(Base):
    """Library of validated legal clauses/provisions."""

    __tablename__ = "clause_library"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    clause_type = Column(String(100), nullable=False, index=True)
    contract_types = Column(ARRAY(String), default=list)  # Applicable contract types
    jurisdictions = Column(ARRAY(String), default=list)  # Valid jurisdictions
    language = Column(String(10), default="en")

    # Classification
    risk_level = Column(String(20), default="low")  # low, medium, high
    favorability = Column(String(20), default="neutral")  # party_a_favorable, neutral, party_b_favorable
    is_standard = Column(Boolean, default=True)
    industry = Column(String(100), nullable=True)

    # Legal Context
    legal_basis = Column(Text, nullable=True)
    related_statutes = Column(JSON, default=list)
    case_precedents = Column(JSON, default=list)
    alternatives = Column(JSON, default=list)

    # Metadata
    version = Column(String(20), default="1.0")
    approved_by = Column(String(255), nullable=True)
    usage_count = Column(Integer, default=0)
    effectiveness_score = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
