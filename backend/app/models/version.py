"""Version control models for legal documents."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer,
    Float, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class ContractVersion(Base):
    """Version history for contracts (git-like versioning)."""

    __tablename__ = "contract_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("version_branches.id"), nullable=True)

    # Content Snapshot
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    clauses_snapshot = Column(JSON, default=list)

    # Change Info
    change_type = Column(String(50), nullable=False)  # created, edited, merged, restored
    change_summary = Column(Text, nullable=True)
    changed_sections = Column(JSON, default=list)

    # Author
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    author_name = Column(String(255), nullable=True)
    author_role = Column(String(100), nullable=True)

    # Approval
    is_approved = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)

    # Metadata
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("contract_versions.id"), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    tags = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    contract = relationship("Contract", back_populates="versions")
    diffs = relationship("VersionDiff", back_populates="version", cascade="all, delete-orphan")
    comments = relationship("VersionComment", back_populates="version", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ContractVersion(contract={self.contract_id}, v={self.version_number})>"


class VersionBranch(Base):
    """Branches for parallel editing of contracts."""

    __tablename__ = "version_branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    branch_type = Column(String(50), default="feature")  # main, feature, review, negotiation

    # Branch State
    is_active = Column(Boolean, default=True)
    is_merged = Column(Boolean, default=False)
    base_version_id = Column(UUID(as_uuid=True), ForeignKey("contract_versions.id"), nullable=True)
    head_version_id = Column(UUID(as_uuid=True), ForeignKey("contract_versions.id"), nullable=True)

    # Ownership
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Merge Info
    merged_at = Column(DateTime(timezone=True), nullable=True)
    merged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    merge_commit_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<VersionBranch(name={self.name}, contract={self.contract_id})>"


class VersionDiff(Base):
    """Track specific changes between versions (redlining)."""

    __tablename__ = "version_diffs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID(as_uuid=True), ForeignKey("contract_versions.id", ondelete="CASCADE"), nullable=False)

    # Diff Details
    diff_type = Column(String(20), nullable=False)  # addition, deletion, modification
    section = Column(String(255), nullable=True)
    clause_number = Column(String(20), nullable=True)
    position_start = Column(Integer, nullable=True)
    position_end = Column(Integer, nullable=True)

    # Content
    original_text = Column(Text, nullable=True)
    modified_text = Column(Text, nullable=True)
    diff_html = Column(Text, nullable=True)  # HTML formatted diff

    # Review
    status = Column(String(20), default="pending")  # pending, accepted, rejected
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_comment = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    version = relationship("ContractVersion", back_populates="diffs")

    def __repr__(self):
        return f"<VersionDiff(type={self.diff_type}, version={self.version_id})>"


class VersionComment(Base):
    """Comments on specific versions or sections."""

    __tablename__ = "version_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID(as_uuid=True), ForeignKey("contract_versions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Comment Details
    content = Column(Text, nullable=False)
    comment_type = Column(String(50), default="general")  # general, suggestion, issue, approval
    clause_reference = Column(String(50), nullable=True)
    position_start = Column(Integer, nullable=True)
    position_end = Column(Integer, nullable=True)

    # Threading
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("version_comments.id"), nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    version = relationship("ContractVersion", back_populates="comments")
