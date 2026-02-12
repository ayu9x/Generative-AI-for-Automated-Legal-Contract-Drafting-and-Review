"""Version control routes for contract versioning."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user, require_role
from app.services.version_control import VersionControlService

router = APIRouter(prefix="/versions", tags=["Version Control"])


# ── Request/Response Schemas ─────────────────────────────────────────

class CreateVersionRequest(BaseModel):
    """Create a new version of a contract."""
    contract_id: str
    content: str
    change_description: str = Field(..., min_length=3, max_length=500)
    branch: str = Field(default="main")


class VersionResponse(BaseModel):
    """Version response."""
    version_id: str
    contract_id: str
    version_number: int
    content_hash: str
    change_description: str
    branch: str
    author_id: str
    author_name: str
    created_at: str
    is_approved: bool = False
    approved_by: Optional[str] = None
    parent_version_id: Optional[str] = None


class VersionHistoryResponse(BaseModel):
    """Version history for a contract."""
    contract_id: str
    versions: List[VersionResponse]
    total_versions: int
    branches: List[str]


class DiffRequest(BaseModel):
    """Request diff between two versions."""
    version_id_a: str
    version_id_b: str


class DiffResponse(BaseModel):
    """Diff between two versions."""
    version_a: str
    version_b: str
    additions: int
    deletions: int
    modifications: int
    diff_lines: List[Dict[str, Any]]
    redline_html: Optional[str] = None


class BranchCreateRequest(BaseModel):
    """Create a new branch."""
    contract_id: str
    branch_name: str = Field(..., min_length=2, max_length=100)
    source_branch: str = Field(default="main")
    description: Optional[str] = None


class BranchResponse(BaseModel):
    """Branch response."""
    branch_id: str
    contract_id: str
    branch_name: str
    source_branch: str
    description: Optional[str] = None
    created_at: str
    created_by: str
    is_merged: bool = False
    version_count: int = 0


class MergeRequest(BaseModel):
    """Merge a branch into target."""
    contract_id: str
    source_branch: str
    target_branch: str = Field(default="main")
    merge_strategy: str = Field(default="auto", description="auto, manual, force")


class MergeResponse(BaseModel):
    """Merge result."""
    merged: bool
    merge_commit_id: Optional[str] = None
    conflicts: List[Dict[str, Any]] = []
    message: str


class VersionCommentRequest(BaseModel):
    """Add a comment to a version."""
    version_id: str
    comment: str
    line_number: Optional[int] = None
    parent_comment_id: Optional[str] = None


class VersionCommentResponse(BaseModel):
    """Version comment."""
    id: str
    version_id: str
    comment: str
    line_number: Optional[int] = None
    author_id: str
    author_name: str
    created_at: str
    resolved: bool = False
    parent_comment_id: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Approve a version."""
    version_id: str
    decision: str = Field(..., description="approve, reject, request_changes")
    comment: Optional[str] = None


class RestoreRequest(BaseModel):
    """Restore a previous version."""
    version_id: str
    reason: str


# ── In-Memory Version Store ─────────────────────────────────────────

_version_service = VersionControlService()


def _version_info_to_response(v, contract_id: str) -> VersionResponse:
    """Convert a VersionInfo model to a VersionResponse."""
    return VersionResponse(
        version_id=v.version_id,
        contract_id=contract_id,
        version_number=v.version_number,
        content_hash=v.content_hash,
        change_description=v.change_summary or "Initial version",
        branch=v.branch or "main",
        author_id=v.created_by,
        author_name=v.created_by,
        created_at=v.created_at.isoformat() if hasattr(v.created_at, "isoformat") else str(v.created_at),
        is_approved=v.is_approved,
        approved_by=None,
        parent_version_id=v.parent_version_id,
    )


def _resolve_version_number(contract_id: str, version_id: str) -> int:
    """Resolve a version_id to its version_number."""
    ver = _version_service.get_version(contract_id, version_id=version_id)
    if not ver:
        raise ValueError(f"Version {version_id} not found")
    return ver["version_number"]


# ── Routes ───────────────────────────────────────────────────────────

@router.post("/", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    request: CreateVersionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new version of a contract."""
    try:
        # Check if this is the first version
        history = _version_service.get_version_history(contract_id=request.contract_id)
        if not history:
            version = _version_service.create_initial_version(
                contract_id=request.contract_id,
                content=request.content,
                created_by=current_user["id"],
            )
        else:
            version = _version_service.create_version(
                contract_id=request.contract_id,
                content=request.content,
                change_summary=request.change_description,
                created_by=current_user["id"],
                branch=request.branch,
            )

        return _version_info_to_response(version, request.contract_id)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create version: {str(e)}",
        )


@router.get("/{contract_id}", response_model=VersionHistoryResponse)
async def get_version_history(
    contract_id: str,
    branch: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Get version history for a contract."""
    history = _version_service.get_version_history(contract_id=contract_id, branch=branch)

    branch_list = _version_service.list_branches(contract_id=contract_id)
    branches = [b.name for b in branch_list] if branch_list else ["main"]

    versions = [_version_info_to_response(v, contract_id) for v in history]

    return VersionHistoryResponse(
        contract_id=contract_id,
        versions=versions,
        total_versions=len(versions),
        branches=branches,
    )


@router.get("/{contract_id}/version/{version_id}")
async def get_version(
    contract_id: str,
    version_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific version."""
    ver = _version_service.get_version(contract_id, version_id=version_id)
    if not ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )
    return {
        "contract_id": contract_id,
        "version_id": ver["version_id"],
        "version_number": ver["version_number"],
        "content_hash": ver["content_hash"],
        "change_description": ver.get("change_summary", ""),
        "branch": ver.get("branch", "main"),
        "author_id": ver["created_by"],
        "author_name": ver["created_by"],
        "created_at": ver["created_at"].isoformat() if hasattr(ver["created_at"], "isoformat") else str(ver["created_at"]),
        "is_approved": ver.get("is_approved", False),
        "content": ver.get("content", ""),
    }


@router.post("/diff", response_model=DiffResponse)
async def compute_diff(
    request: DiffRequest,
    contract_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """Compute diff between two versions."""
    try:
        from_num = _resolve_version_number(contract_id, request.version_id_a)
        to_num = _resolve_version_number(contract_id, request.version_id_b)

        diffs = _version_service.compute_diff(
            contract_id=contract_id,
            from_version=from_num,
            to_version=to_num,
        )

        redline_html = _version_service.generate_redline_html(
            contract_id=contract_id,
            from_version=from_num,
            to_version=to_num,
        )

        additions = sum(1 for d in diffs if d.diff_type == "addition")
        deletions = sum(1 for d in diffs if d.diff_type == "deletion")
        modifications = sum(1 for d in diffs if d.diff_type == "modification")

        diff_lines = [
            {
                "type": d.diff_type,
                "line_start": d.line_start,
                "line_end": d.line_end,
                "original_text": d.original_text,
                "modified_text": d.modified_text,
                "section": d.section,
            }
            for d in diffs
        ]

        return DiffResponse(
            version_a=request.version_id_a,
            version_b=request.version_id_b,
            additions=additions,
            deletions=deletions,
            modifications=modifications,
            diff_lines=diff_lines,
            redline_html=redline_html,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to compute diff: {str(e)}",
        )


@router.post("/branches", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    request: BranchCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new branch for a contract."""
    try:
        branch = _version_service.create_branch(
            contract_id=request.contract_id,
            branch_name=request.branch_name,
            branch_type=request.source_branch,
            created_by=current_user["id"],
        )

        return BranchResponse(
            branch_id=branch.branch_id,
            contract_id=request.contract_id,
            branch_name=branch.name,
            source_branch=request.source_branch,
            description=request.description,
            created_at=branch.created_at.isoformat() if hasattr(branch.created_at, "isoformat") else str(branch.created_at),
            created_by=branch.created_by,
            is_merged=branch.is_merged,
            version_count=max(0, branch.head_version - branch.base_version + 1),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create branch: {str(e)}",
        )


@router.get("/{contract_id}/branches", response_model=List[BranchResponse])
async def list_branches(
    contract_id: str,
    current_user: dict = Depends(get_current_user),
):
    """List all branches for a contract."""
    branches = _version_service.list_branches(contract_id=contract_id)

    return [
        BranchResponse(
            branch_id=b.branch_id,
            contract_id=contract_id,
            branch_name=b.name,
            source_branch=b.branch_type,
            description=None,
            created_at=b.created_at.isoformat() if hasattr(b.created_at, "isoformat") else str(b.created_at),
            created_by=b.created_by,
            is_merged=b.is_merged,
            version_count=max(0, b.head_version - b.base_version + 1),
        )
        for b in branches
    ]


@router.post("/merge", response_model=MergeResponse)
async def merge_branches(
    request: MergeRequest,
    current_user: dict = Depends(require_role("ADMIN", "LEGAL_ADMIN", "SENIOR_ATTORNEY")),
):
    """Merge a branch into the target branch."""
    try:
        result = _version_service.merge_branch(
            contract_id=request.contract_id,
            source_branch=request.source_branch,
            target_branch=request.target_branch,
            merged_by=current_user["id"],
        )

        return MergeResponse(
            merged=result.success,
            merge_commit_id=result.merge_version_id,
            conflicts=result.conflicts,
            message=f"Merge {'completed' if result.success else 'failed'}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Merge failed: {str(e)}",
        )


@router.post("/approve")
async def approve_version(
    request: ApprovalRequest,
    contract_id: str = Query(...),
    current_user: dict = Depends(require_role("ADMIN", "LEGAL_ADMIN", "SENIOR_ATTORNEY")),
):
    """Approve, reject, or request changes for a version."""
    if request.decision == "approve":
        try:
            version_number = _resolve_version_number(contract_id, request.version_id)
            success = _version_service.approve_version(
                contract_id=contract_id,
                version_number=version_number,
                approved_by=current_user["id"],
                notes=request.comment,
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Version not found",
                )
            return {"message": "Version approved", "version_id": request.version_id}
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Approval failed: {str(e)}",
            )
    elif request.decision == "reject":
        return {
            "message": "Version rejected",
            "version_id": request.version_id,
            "comment": request.comment,
        }
    else:
        return {
            "message": "Changes requested",
            "version_id": request.version_id,
            "comment": request.comment,
        }


@router.post("/restore")
async def restore_version(
    request: RestoreRequest,
    contract_id: str = Query(...),
    current_user: dict = Depends(require_role("ADMIN", "LEGAL_ADMIN")),
):
    """Restore a previous version of a contract."""
    try:
        version_number = _resolve_version_number(contract_id, request.version_id)
        result = _version_service.restore_version(
            contract_id=contract_id,
            version_number=version_number,
            restored_by=current_user["id"],
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found",
            )
        return {
            "message": "Version restored successfully",
            "new_version_id": result.version_id,
            "restored_from": request.version_id,
            "reason": request.reason,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Restore failed: {str(e)}",
        )


@router.post("/comments", response_model=VersionCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    request: VersionCommentRequest,
    contract_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """Add a comment to a specific version."""
    try:
        version_number = _resolve_version_number(contract_id, request.version_id)
        comment = _version_service.add_comment(
            contract_id=contract_id,
            version_number=version_number,
            user_id=current_user["id"],
            content=request.comment,
            parent_comment_id=request.parent_comment_id,
        )

        created_at = comment["created_at"]
        if hasattr(created_at, "isoformat"):
            created_at = created_at.isoformat()

        return VersionCommentResponse(
            id=comment["comment_id"],
            version_id=request.version_id,
            comment=comment["content"],
            line_number=request.line_number,
            author_id=comment["user_id"],
            author_name=comment["user_id"],
            created_at=str(created_at),
            resolved=comment.get("is_resolved", False),
            parent_comment_id=comment.get("parent_comment_id"),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add comment: {str(e)}",
        )


@router.get("/comments/{version_id}", response_model=List[VersionCommentResponse])
async def get_comments(
    version_id: str,
    contract_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """Get comments for a specific version."""
    try:
        version_number = _resolve_version_number(contract_id, version_id)
        comments = _version_service.get_comments(
            contract_id=contract_id,
            version_number=version_number,
        )

        result = []
        for c in comments:
            created_at = c["created_at"]
            if hasattr(created_at, "isoformat"):
                created_at = created_at.isoformat()

            result.append(VersionCommentResponse(
                id=c["comment_id"],
                version_id=version_id,
                comment=c["content"],
                line_number=None,
                author_id=c["user_id"],
                author_name=c["user_id"],
                created_at=str(created_at),
                resolved=c.get("is_resolved", False),
                parent_comment_id=c.get("parent_comment_id"),
            ))
        return result
    except ValueError:
        return []


@router.put("/comments/{comment_id}/resolve")
async def resolve_version_comment(
    comment_id: str,
    contract_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    """Resolve a version comment."""
    try:
        success = _version_service.resolve_comment(
            comment_id=comment_id,
            resolved_by=current_user["id"],
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found",
            )
        return {"message": "Comment resolved", "comment_id": comment_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to resolve comment: {str(e)}",
        )
