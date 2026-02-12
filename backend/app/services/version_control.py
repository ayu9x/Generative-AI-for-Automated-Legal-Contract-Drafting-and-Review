"""Version Control Service - Git-like versioning for legal documents."""

import uuid
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import structlog
from pydantic import BaseModel, Field

from app.core.security import hash_document

logger = structlog.get_logger(__name__)


# ─── Version Control Schemas ────────────────────────────────────────────

class VersionInfo(BaseModel):
    """Version information."""
    version_id: str
    version_number: int
    content_hash: str
    change_type: str
    change_summary: str
    created_by: str
    created_at: datetime
    branch: Optional[str] = None
    parent_version_id: Optional[str] = None
    is_approved: bool = False
    tags: List[str] = Field(default_factory=list)


class DiffEntry(BaseModel):
    """A single diff entry between versions."""
    diff_type: str  # addition, deletion, modification
    line_start: int
    line_end: int
    original_text: Optional[str] = None
    modified_text: Optional[str] = None
    section: Optional[str] = None


class BranchInfo(BaseModel):
    """Branch information."""
    branch_id: str
    name: str
    branch_type: str
    is_active: bool
    base_version: int
    head_version: int
    created_by: str
    created_at: datetime
    is_merged: bool = False


class MergeResult(BaseModel):
    """Result of a branch merge."""
    success: bool
    merged_content: Optional[str] = None
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    merge_version_id: Optional[str] = None
    changes_applied: int = 0


# ─── Version Control Engine ─────────────────────────────────────────────

class VersionControlService:
    """Git-like version control for legal documents with redlining support."""

    def __init__(self):
        # In-memory storage for demo (would use DB in production)
        self._versions: Dict[str, List[Dict[str, Any]]] = {}
        self._branches: Dict[str, List[Dict[str, Any]]] = {}
        self._comments: Dict[str, List[Dict[str, Any]]] = {}

    def create_initial_version(
        self,
        contract_id: str,
        content: str,
        created_by: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VersionInfo:
        """Create the initial version of a contract."""
        version_id = str(uuid.uuid4())
        content_hash = hash_document(content)

        version = {
            "version_id": version_id,
            "version_number": 1,
            "content": content,
            "content_hash": content_hash,
            "change_type": "created",
            "change_summary": "Initial version",
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc),
            "branch": "main",
            "parent_version_id": None,
            "is_approved": False,
            "tags": [],
            "metadata": metadata or {},
        }

        if contract_id not in self._versions:
            self._versions[contract_id] = []

        self._versions[contract_id].append(version)

        # Create main branch
        self._create_branch_internal(
            contract_id, "main", "main", version_id, created_by
        )

        logger.info(
            "Initial version created",
            contract_id=contract_id,
            version_id=version_id,
        )

        return VersionInfo(**{k: v for k, v in version.items() if k != "content" and k != "metadata"})

    def create_version(
        self,
        contract_id: str,
        content: str,
        change_summary: str,
        created_by: str,
        change_type: str = "edited",
        branch: str = "main",
        tags: Optional[List[str]] = None,
    ) -> VersionInfo:
        """Create a new version of a contract."""
        versions = self._versions.get(contract_id, [])
        if not versions:
            return self.create_initial_version(contract_id, content, created_by)

        # Get latest version on this branch
        branch_versions = [v for v in versions if v.get("branch") == branch]
        if not branch_versions:
            branch_versions = versions

        latest = max(branch_versions, key=lambda v: v["version_number"])
        new_version_number = latest["version_number"] + 1
        content_hash = hash_document(content)

        # Check if content actually changed
        if content_hash == latest["content_hash"]:
            logger.info("No content changes detected, skipping version creation")
            return VersionInfo(**{k: v for k, v in latest.items() if k != "content" and k != "metadata"})

        version_id = str(uuid.uuid4())
        version = {
            "version_id": version_id,
            "version_number": new_version_number,
            "content": content,
            "content_hash": content_hash,
            "change_type": change_type,
            "change_summary": change_summary,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc),
            "branch": branch,
            "parent_version_id": latest["version_id"],
            "is_approved": False,
            "tags": tags or [],
        }

        self._versions[contract_id].append(version)

        logger.info(
            "New version created",
            contract_id=contract_id,
            version_id=version_id,
            version_number=new_version_number,
        )

        return VersionInfo(**{k: v for k, v in version.items() if k != "content" and k != "metadata"})

    def get_version(
        self,
        contract_id: str,
        version_number: Optional[int] = None,
        version_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get a specific version of a contract."""
        versions = self._versions.get(contract_id, [])

        if version_id:
            for v in versions:
                if v["version_id"] == version_id:
                    return v
        elif version_number:
            for v in versions:
                if v["version_number"] == version_number:
                    return v
        elif versions:
            return max(versions, key=lambda v: v["version_number"])

        return None

    def get_version_history(
        self,
        contract_id: str,
        branch: Optional[str] = None,
        limit: int = 50,
    ) -> List[VersionInfo]:
        """Get version history for a contract."""
        versions = self._versions.get(contract_id, [])

        if branch:
            versions = [v for v in versions if v.get("branch") == branch]

        versions = sorted(versions, key=lambda v: v["version_number"], reverse=True)[:limit]

        return [
            VersionInfo(**{k: v for k, v in ver.items() if k != "content" and k != "metadata"})
            for ver in versions
        ]

    def compute_diff(
        self,
        contract_id: str,
        from_version: int,
        to_version: int,
    ) -> List[DiffEntry]:
        """Compute diff between two versions (redlining)."""
        v1 = self.get_version(contract_id, version_number=from_version)
        v2 = self.get_version(contract_id, version_number=to_version)

        if not v1 or not v2:
            return []

        old_lines = v1["content"].splitlines()
        new_lines = v2["content"].splitlines()

        diffs = []

        # Simple line-by-line diff (production would use diff-match-patch)
        try:
            import difflib
            differ = difflib.unified_diff(
                old_lines, new_lines,
                fromfile=f"v{from_version}",
                tofile=f"v{to_version}",
                lineterm="",
            )

            line_num = 0
            for line in differ:
                if line.startswith("---") or line.startswith("+++"):
                    continue
                elif line.startswith("@@"):
                    # Parse hunk header
                    import re
                    match = re.search(r'\+(\d+)', line)
                    if match:
                        line_num = int(match.group(1))
                    continue
                elif line.startswith("-"):
                    diffs.append(DiffEntry(
                        diff_type="deletion",
                        line_start=line_num,
                        line_end=line_num,
                        original_text=line[1:],
                        modified_text=None,
                    ))
                elif line.startswith("+"):
                    diffs.append(DiffEntry(
                        diff_type="addition",
                        line_start=line_num,
                        line_end=line_num,
                        original_text=None,
                        modified_text=line[1:],
                    ))
                    line_num += 1
                else:
                    line_num += 1

        except Exception as e:
            logger.error(f"Diff computation failed: {e}")

        return diffs

    def generate_redline_html(
        self,
        contract_id: str,
        from_version: int,
        to_version: int,
    ) -> str:
        """Generate HTML redline document showing changes."""
        diffs = self.compute_diff(contract_id, from_version, to_version)

        v2 = self.get_version(contract_id, version_number=to_version)
        if not v2:
            return ""

        html = """
        <html>
        <head>
            <style>
                body { font-family: 'Times New Roman', serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .addition { background-color: #e6ffe6; color: #006600; text-decoration: underline; }
                .deletion { background-color: #ffe6e6; color: #cc0000; text-decoration: line-through; }
                .unchanged { color: #333; }
                .header { text-align: center; margin-bottom: 30px; }
                .version-info { font-size: 12px; color: #666; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Redline Comparison</h2>
                <div class="version-info">
                    Comparing Version {from_v} → Version {to_v}
                </div>
            </div>
        """.format(from_v=from_version, to_v=to_version)

        for diff in diffs:
            if diff.diff_type == "deletion":
                html += f'<span class="deletion">{diff.original_text}</span>\n'
            elif diff.diff_type == "addition":
                html += f'<span class="addition">{diff.modified_text}</span>\n'

        html += "</body></html>"
        return html

    # ─── Branch Management ───────────────────────────────────────────────

    def create_branch(
        self,
        contract_id: str,
        branch_name: str,
        branch_type: str,
        created_by: str,
        base_version: Optional[int] = None,
    ) -> BranchInfo:
        """Create a new branch for parallel editing."""
        versions = self._versions.get(contract_id, [])
        if not versions:
            raise ValueError(f"No versions found for contract {contract_id}")

        # Get base version
        if base_version:
            base = self.get_version(contract_id, version_number=base_version)
        else:
            base = max(versions, key=lambda v: v["version_number"])

        if not base:
            raise ValueError("Base version not found")

        return self._create_branch_internal(
            contract_id, branch_name, branch_type,
            base["version_id"], created_by,
        )

    def _create_branch_internal(
        self,
        contract_id: str,
        branch_name: str,
        branch_type: str,
        base_version_id: str,
        created_by: str,
    ) -> BranchInfo:
        """Internal method to create a branch."""
        branch_id = str(uuid.uuid4())

        branch = {
            "branch_id": branch_id,
            "contract_id": contract_id,
            "name": branch_name,
            "branch_type": branch_type,
            "is_active": True,
            "base_version_id": base_version_id,
            "head_version_id": base_version_id,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc),
            "is_merged": False,
        }

        if contract_id not in self._branches:
            self._branches[contract_id] = []

        self._branches[contract_id].append(branch)

        # Find version number from version_id
        versions = self._versions.get(contract_id, [])
        base_version_num = 1
        for v in versions:
            if v["version_id"] == base_version_id:
                base_version_num = v["version_number"]
                break

        return BranchInfo(
            branch_id=branch_id,
            name=branch_name,
            branch_type=branch_type,
            is_active=True,
            base_version=base_version_num,
            head_version=base_version_num,
            created_by=created_by,
            created_at=branch["created_at"],
        )

    def list_branches(self, contract_id: str) -> List[BranchInfo]:
        """List all branches for a contract."""
        branches = self._branches.get(contract_id, [])
        result = []

        for b in branches:
            versions = self._versions.get(contract_id, [])
            base_num = 1
            head_num = 1
            for v in versions:
                if v["version_id"] == b["base_version_id"]:
                    base_num = v["version_number"]
                if v["version_id"] == b["head_version_id"]:
                    head_num = v["version_number"]

            result.append(BranchInfo(
                branch_id=b["branch_id"],
                name=b["name"],
                branch_type=b["branch_type"],
                is_active=b["is_active"],
                base_version=base_num,
                head_version=head_num,
                created_by=b["created_by"],
                created_at=b["created_at"],
                is_merged=b["is_merged"],
            ))

        return result

    def merge_branch(
        self,
        contract_id: str,
        source_branch: str,
        target_branch: str = "main",
        merged_by: str = "system",
    ) -> MergeResult:
        """Merge one branch into another."""
        branches = self._branches.get(contract_id, [])
        source = None
        target = None

        for b in branches:
            if b["name"] == source_branch:
                source = b
            if b["name"] == target_branch:
                target = b

        if not source or not target:
            return MergeResult(
                success=False,
                conflicts=[{"error": f"Branch not found: {source_branch if not source else target_branch}"}],
            )

        # Get latest versions from each branch
        versions = self._versions.get(contract_id, [])
        source_versions = [v for v in versions if v.get("branch") == source_branch]
        target_versions = [v for v in versions if v.get("branch") == target_branch]

        if not source_versions:
            return MergeResult(success=False, conflicts=[{"error": "No versions in source branch"}])

        latest_source = max(source_versions, key=lambda v: v["version_number"])
        latest_target = max(target_versions, key=lambda v: v["version_number"]) if target_versions else None

        # Simple merge: apply source content to target branch
        merged_content = latest_source["content"]

        # Check for conflicts (simplified)
        conflicts = []
        if latest_target and latest_target["content_hash"] != latest_source.get("parent_content_hash", ""):
            # Both branches modified - potential conflict
            # In production, use 3-way merge algorithm
            pass

        # Create merge version
        merge_version = self.create_version(
            contract_id=contract_id,
            content=merged_content,
            change_summary=f"Merged branch '{source_branch}' into '{target_branch}'",
            created_by=merged_by,
            change_type="merged",
            branch=target_branch,
            tags=["merge"],
        )

        # Mark source branch as merged
        source["is_merged"] = True
        source["is_active"] = False

        return MergeResult(
            success=True,
            merged_content=merged_content,
            conflicts=conflicts,
            merge_version_id=merge_version.version_id,
            changes_applied=1,
        )

    def approve_version(
        self,
        contract_id: str,
        version_number: int,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> bool:
        """Approve a specific version."""
        version = self.get_version(contract_id, version_number=version_number)
        if not version:
            return False

        version["is_approved"] = True
        version["approved_by"] = approved_by
        version["approved_at"] = datetime.now(timezone.utc)
        version["approval_notes"] = notes

        logger.info(
            "Version approved",
            contract_id=contract_id,
            version_number=version_number,
            approved_by=approved_by,
        )

        return True

    def restore_version(
        self,
        contract_id: str,
        version_number: int,
        restored_by: str,
    ) -> Optional[VersionInfo]:
        """Restore a previous version as the current version."""
        old_version = self.get_version(contract_id, version_number=version_number)
        if not old_version:
            return None

        return self.create_version(
            contract_id=contract_id,
            content=old_version["content"],
            change_summary=f"Restored from version {version_number}",
            created_by=restored_by,
            change_type="restored",
        )

    # ─── Comment System ──────────────────────────────────────────────────

    def add_comment(
        self,
        contract_id: str,
        version_number: int,
        user_id: str,
        content: str,
        comment_type: str = "general",
        clause_reference: Optional[str] = None,
        parent_comment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a comment to a specific version."""
        comment = {
            "comment_id": str(uuid.uuid4()),
            "contract_id": contract_id,
            "version_number": version_number,
            "user_id": user_id,
            "content": content,
            "comment_type": comment_type,
            "clause_reference": clause_reference,
            "parent_comment_id": parent_comment_id,
            "is_resolved": False,
            "created_at": datetime.now(timezone.utc),
        }

        key = f"{contract_id}:{version_number}"
        if key not in self._comments:
            self._comments[key] = []
        self._comments[key].append(comment)

        return comment

    def get_comments(
        self,
        contract_id: str,
        version_number: int,
    ) -> List[Dict[str, Any]]:
        """Get comments for a specific version."""
        key = f"{contract_id}:{version_number}"
        return self._comments.get(key, [])

    def resolve_comment(
        self,
        comment_id: str,
        resolved_by: str,
    ) -> bool:
        """Mark a comment as resolved."""
        for key, comments in self._comments.items():
            for comment in comments:
                if comment["comment_id"] == comment_id:
                    comment["is_resolved"] = True
                    comment["resolved_by"] = resolved_by
                    comment["resolved_at"] = datetime.now(timezone.utc)
                    return True
        return False


# Singleton instance
version_control = VersionControlService()
