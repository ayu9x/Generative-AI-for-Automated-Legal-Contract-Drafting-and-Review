"""Contract review and risk analysis routes."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user, require_role
from app.services.risk_analyzer import RiskAnalyzer

router = APIRouter(prefix="/review", tags=["Contract Review"])


# ── Request/Response Schemas ─────────────────────────────────────────

class RiskAnalysisRequest(BaseModel):
    """Request risk analysis for a contract."""
    contract_id: Optional[str] = None
    content: Optional[str] = None
    contract_type: str = Field(default="general")
    jurisdiction: str = Field(default="US-Federal")
    include_ai_analysis: bool = True


class RiskFactorResponse(BaseModel):
    """Individual risk factor."""
    category: str
    name: str
    severity: str
    description: str
    recommendation: str
    clause_reference: Optional[str] = None
    confidence: float = 0.0


class RiskAnalysisResponse(BaseModel):
    """Complete risk analysis response."""
    analysis_id: str
    contract_id: Optional[str] = None
    overall_risk_score: float
    risk_level: str
    total_factors: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    risk_factors: List[RiskFactorResponse]
    category_scores: Dict[str, float]
    executive_summary: str
    recommendations: List[str]
    analyzed_at: str


class BatchRiskRequest(BaseModel):
    """Batch risk analysis request."""
    contracts: List[RiskAnalysisRequest]


class BatchRiskResponse(BaseModel):
    """Batch risk analysis response."""
    results: List[RiskAnalysisResponse]
    total_analyzed: int
    average_risk_score: float
    highest_risk_contract: Optional[str] = None


class ReviewCommentRequest(BaseModel):
    """Add a review comment."""
    contract_id: str
    section: Optional[str] = None
    comment: str
    severity: str = Field(default="info", description="info, warning, critical")


class ReviewCommentResponse(BaseModel):
    """Review comment response."""
    id: str
    contract_id: str
    section: Optional[str] = None
    comment: str
    severity: str
    author_id: str
    author_name: str
    created_at: str
    resolved: bool = False


class ReviewStatusResponse(BaseModel):
    """Overall review status."""
    contract_id: str
    status: str
    risk_score: Optional[float] = None
    compliance_score: Optional[float] = None
    comments_count: int
    unresolved_comments: int
    last_reviewed: Optional[str] = None
    reviewers: List[str]


# ── In-Memory Stores ────────────────────────────────────────────────

_analyses_db: Dict[str, Dict] = {}
_comments_db: Dict[str, List[Dict]] = {}
_review_status_db: Dict[str, Dict] = {}

_risk_analyzer = RiskAnalyzer()


# ── Routes ───────────────────────────────────────────────────────────

@router.post("/risk-analysis", response_model=RiskAnalysisResponse)
async def analyze_risk(
    request: RiskAnalysisRequest,
    current_user: dict = Depends(get_current_user),
):
    """Perform risk analysis on a contract."""
    # Get contract content
    content = request.content
    if not content and request.contract_id:
        from app.api.routes.contracts import _contracts_db
        contract = _contracts_db.get(request.contract_id)
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found",
            )
        content = contract["content"]

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either contract_id or content must be provided",
        )

    try:
        result = await _risk_analyzer.analyze(
            content=content,
            contract_type=request.contract_type,
            jurisdiction=request.jurisdiction,
        )

        analysis_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        risk_factors = []
        critical = high = medium = low = 0
        for factor in result.get("risk_factors", []):
            severity = factor.get("severity", "medium")
            if severity == "critical":
                critical += 1
            elif severity == "high":
                high += 1
            elif severity == "medium":
                medium += 1
            else:
                low += 1

            risk_factors.append(RiskFactorResponse(
                category=factor.get("category", "general"),
                name=factor.get("name", "Unknown"),
                severity=severity,
                description=factor.get("description", ""),
                recommendation=factor.get("recommendation", "Review required"),
                clause_reference=factor.get("clause_reference"),
                confidence=factor.get("confidence", 0.7),
            ))

        overall_score = result.get("overall_risk_score", 0.5)
        risk_level = (
            "critical" if overall_score >= 0.8
            else "high" if overall_score >= 0.6
            else "medium" if overall_score >= 0.4
            else "low"
        )

        analysis = RiskAnalysisResponse(
            analysis_id=analysis_id,
            contract_id=request.contract_id,
            overall_risk_score=overall_score,
            risk_level=risk_level,
            total_factors=len(risk_factors),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            risk_factors=risk_factors,
            category_scores=result.get("category_scores", {}),
            executive_summary=result.get("executive_summary", "Risk analysis complete."),
            recommendations=result.get("recommendations", []),
            analyzed_at=now,
        )

        _analyses_db[analysis_id] = analysis.model_dump()

        # Update review status
        if request.contract_id:
            _update_review_status(request.contract_id, risk_score=overall_score)

        return analysis

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk analysis failed: {str(e)}",
        )


@router.post("/batch-analysis", response_model=BatchRiskResponse)
async def batch_risk_analysis(
    request: BatchRiskRequest,
    current_user: dict = Depends(require_role("ADMIN", "LEGAL_ADMIN", "SENIOR_ATTORNEY")),
):
    """Perform risk analysis on multiple contracts."""
    results = []
    for contract_req in request.contracts:
        try:
            result = await analyze_risk(contract_req, current_user)
            results.append(result)
        except HTTPException:
            continue

    avg_score = (
        sum(r.overall_risk_score for r in results) / len(results) if results else 0.0
    )
    highest_risk = max(results, key=lambda r: r.overall_risk_score) if results else None

    return BatchRiskResponse(
        results=results,
        total_analyzed=len(results),
        average_risk_score=avg_score,
        highest_risk_contract=highest_risk.contract_id if highest_risk else None,
    )


@router.get("/analysis/{analysis_id}", response_model=RiskAnalysisResponse)
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific risk analysis result."""
    analysis = _analyses_db.get(analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )
    return RiskAnalysisResponse(**analysis)


@router.get("/history/{contract_id}")
async def get_analysis_history(
    contract_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get risk analysis history for a contract."""
    history = [
        a for a in _analyses_db.values()
        if a.get("contract_id") == contract_id
    ]
    history.sort(key=lambda a: a.get("analyzed_at", ""), reverse=True)
    return {"contract_id": contract_id, "analyses": history, "total": len(history)}


@router.post("/comments", response_model=ReviewCommentResponse, status_code=status.HTTP_201_CREATED)
async def add_review_comment(
    request: ReviewCommentRequest,
    current_user: dict = Depends(get_current_user),
):
    """Add a review comment to a contract."""
    comment_id = str(uuid4())
    now = datetime.utcnow().isoformat()

    comment = {
        "id": comment_id,
        "contract_id": request.contract_id,
        "section": request.section,
        "comment": request.comment,
        "severity": request.severity,
        "author_id": current_user["id"],
        "author_name": current_user["full_name"],
        "created_at": now,
        "resolved": False,
    }

    if request.contract_id not in _comments_db:
        _comments_db[request.contract_id] = []
    _comments_db[request.contract_id].append(comment)

    _update_review_status(request.contract_id)

    return ReviewCommentResponse(**comment)


@router.get("/comments/{contract_id}", response_model=List[ReviewCommentResponse])
async def get_review_comments(
    contract_id: str,
    resolved: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
):
    """Get review comments for a contract."""
    comments = _comments_db.get(contract_id, [])
    if resolved is not None:
        comments = [c for c in comments if c["resolved"] == resolved]
    return [ReviewCommentResponse(**c) for c in comments]


@router.put("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Mark a review comment as resolved."""
    for contract_comments in _comments_db.values():
        for comment in contract_comments:
            if comment["id"] == comment_id:
                comment["resolved"] = True
                return {"message": "Comment resolved", "comment_id": comment_id}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Comment not found",
    )


@router.get("/status/{contract_id}", response_model=ReviewStatusResponse)
async def get_review_status(
    contract_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get the overall review status of a contract."""
    status_data = _review_status_db.get(contract_id)
    if not status_data:
        comments = _comments_db.get(contract_id, [])
        return ReviewStatusResponse(
            contract_id=contract_id,
            status="not_reviewed",
            comments_count=len(comments),
            unresolved_comments=len([c for c in comments if not c["resolved"]]),
            reviewers=[],
        )

    return ReviewStatusResponse(**status_data)


# ── Helpers ──────────────────────────────────────────────────────────

def _update_review_status(contract_id: str, risk_score: float = None, compliance_score: float = None):
    """Update the review status for a contract."""
    comments = _comments_db.get(contract_id, [])
    unresolved = [c for c in comments if not c["resolved"]]
    reviewers = list(set(c["author_name"] for c in comments))

    existing = _review_status_db.get(contract_id, {})

    _review_status_db[contract_id] = {
        "contract_id": contract_id,
        "status": "in_review",
        "risk_score": risk_score or existing.get("risk_score"),
        "compliance_score": compliance_score or existing.get("compliance_score"),
        "comments_count": len(comments),
        "unresolved_comments": len(unresolved),
        "last_reviewed": datetime.utcnow().isoformat(),
        "reviewers": reviewers,
    }
