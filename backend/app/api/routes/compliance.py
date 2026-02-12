"""Compliance checking and regulatory routes."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user, require_role
from app.services.compliance_checker import ComplianceChecker

router = APIRouter(prefix="/compliance", tags=["Compliance"])


# ── Request/Response Schemas ─────────────────────────────────────────

class ComplianceCheckRequest(BaseModel):
    """Request compliance check for a contract."""
    contract_id: Optional[str] = None
    content: Optional[str] = None
    contract_type: str = Field(default="general")
    jurisdictions: List[str] = Field(default=["US-Federal"])
    frameworks: List[str] = Field(
        default=["general"],
        description="Compliance frameworks: gdpr, hipaa, sox, ccpa, employment, general, international, anti_corruption",
    )
    include_ai_analysis: bool = True


class ComplianceRuleResult(BaseModel):
    """Individual compliance rule result."""
    rule_id: str
    rule_name: str
    framework: str
    category: str
    status: str  # compliant, non_compliant, partial, not_applicable
    severity: str
    description: str
    finding: Optional[str] = None
    recommendation: Optional[str] = None
    clause_reference: Optional[str] = None


class ComplianceCheckResponse(BaseModel):
    """Complete compliance check response."""
    check_id: str
    contract_id: Optional[str] = None
    overall_score: float
    compliance_status: str  # compliant, non_compliant, partially_compliant
    total_rules_checked: int
    compliant_count: int
    non_compliant_count: int
    partial_count: int
    not_applicable_count: int
    rule_results: List[ComplianceRuleResult]
    framework_scores: Dict[str, float]
    jurisdictions_checked: List[str]
    critical_violations: List[Dict[str, Any]]
    recommendations: List[str]
    checked_at: str


class JurisdictionInfoResponse(BaseModel):
    """Jurisdiction information."""
    code: str
    name: str
    legal_system: str
    applicable_frameworks: List[str]
    key_requirements: List[str]


class ComplianceReportRequest(BaseModel):
    """Generate a compliance report."""
    contract_id: str
    include_risk_analysis: bool = True
    include_recommendations: bool = True
    format: str = Field(default="detailed", description="summary, detailed, executive")


class ComplianceReportResponse(BaseModel):
    """Compliance report response."""
    report_id: str
    contract_id: str
    generated_at: str
    format: str
    overall_compliance_score: float
    sections: List[Dict[str, Any]]
    executive_summary: str


class RegulatoryUpdateResponse(BaseModel):
    """Regulatory update notification."""
    id: str
    framework: str
    jurisdiction: str
    title: str
    description: str
    impact_level: str
    effective_date: str
    published_date: str
    action_required: bool


# ── In-Memory Stores ────────────────────────────────────────────────

_compliance_checks_db: Dict[str, Dict] = {}
_compliance_checker = ComplianceChecker()

# Supported jurisdictions
JURISDICTIONS = {
    "US-Federal": {
        "code": "US-Federal",
        "name": "United States - Federal",
        "legal_system": "common_law",
        "applicable_frameworks": ["general", "sox", "anti_corruption"],
        "key_requirements": ["Contract must be in English", "Consider UCC provisions", "Federal regulations apply"],
    },
    "US-CA": {
        "code": "US-CA",
        "name": "United States - California",
        "legal_system": "common_law",
        "applicable_frameworks": ["general", "ccpa"],
        "key_requirements": ["CCPA compliance required", "Cal. Civil Code provisions", "Non-compete restrictions"],
    },
    "EU": {
        "code": "EU",
        "name": "European Union",
        "legal_system": "civil_law",
        "applicable_frameworks": ["general", "gdpr"],
        "key_requirements": ["GDPR compliance mandatory", "Consumer protection directives", "Data transfer restrictions"],
    },
    "UK": {
        "code": "UK",
        "name": "United Kingdom",
        "legal_system": "common_law",
        "applicable_frameworks": ["general", "gdpr"],
        "key_requirements": ["UK GDPR applies", "Consumer Rights Act 2015", "Unfair Contract Terms Act 1977"],
    },
    "HIPAA": {
        "code": "HIPAA",
        "name": "HIPAA Covered Entities",
        "legal_system": "regulatory",
        "applicable_frameworks": ["hipaa", "general"],
        "key_requirements": ["BAA required for PHI", "Security Rule compliance", "Breach notification procedures"],
    },
}


# ── Routes ───────────────────────────────────────────────────────────

@router.post("/check", response_model=ComplianceCheckResponse)
async def check_compliance(
    request: ComplianceCheckRequest,
    current_user: dict = Depends(get_current_user),
):
    """Perform compliance check on a contract."""
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
        result = await _compliance_checker.check_compliance(
            content=content,
            contract_type=request.contract_type,
            jurisdictions=request.jurisdictions,
            frameworks=request.frameworks,
        )

        check_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        rule_results = []
        compliant = non_compliant = partial = not_applicable = 0
        critical_violations = []

        for rule in result.get("rule_results", []):
            rule_status = rule.get("status", "not_applicable")
            if rule_status == "compliant":
                compliant += 1
            elif rule_status == "non_compliant":
                non_compliant += 1
                if rule.get("severity") in ("critical", "high"):
                    critical_violations.append({
                        "rule": rule.get("rule_name", ""),
                        "framework": rule.get("framework", ""),
                        "severity": rule.get("severity", ""),
                        "finding": rule.get("finding", ""),
                    })
            elif rule_status == "partial":
                partial += 1
            else:
                not_applicable += 1

            rule_results.append(ComplianceRuleResult(
                rule_id=rule.get("rule_id", str(uuid4())),
                rule_name=rule.get("rule_name", "Unknown Rule"),
                framework=rule.get("framework", "general"),
                category=rule.get("category", "general"),
                status=rule_status,
                severity=rule.get("severity", "medium"),
                description=rule.get("description", ""),
                finding=rule.get("finding"),
                recommendation=rule.get("recommendation"),
                clause_reference=rule.get("clause_reference"),
            ))

        total = compliant + non_compliant + partial + not_applicable
        overall_score = result.get("overall_score", 0.0)

        compliance_status = (
            "compliant" if overall_score >= 0.9
            else "partially_compliant" if overall_score >= 0.6
            else "non_compliant"
        )

        response = ComplianceCheckResponse(
            check_id=check_id,
            contract_id=request.contract_id,
            overall_score=overall_score,
            compliance_status=compliance_status,
            total_rules_checked=total,
            compliant_count=compliant,
            non_compliant_count=non_compliant,
            partial_count=partial,
            not_applicable_count=not_applicable,
            rule_results=rule_results,
            framework_scores=result.get("framework_scores", {}),
            jurisdictions_checked=request.jurisdictions,
            critical_violations=critical_violations,
            recommendations=result.get("recommendations", []),
            checked_at=now,
        )

        _compliance_checks_db[check_id] = response.model_dump()

        # Update review status
        if request.contract_id:
            from app.api.routes.review import _update_review_status
            _update_review_status(request.contract_id, compliance_score=overall_score)

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance check failed: {str(e)}",
        )


@router.get("/check/{check_id}", response_model=ComplianceCheckResponse)
async def get_compliance_check(
    check_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific compliance check result."""
    check = _compliance_checks_db.get(check_id)
    if not check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compliance check not found",
        )
    return ComplianceCheckResponse(**check)


@router.get("/history/{contract_id}")
async def get_compliance_history(
    contract_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get compliance check history for a contract."""
    history = [
        c for c in _compliance_checks_db.values()
        if c.get("contract_id") == contract_id
    ]
    history.sort(key=lambda c: c.get("checked_at", ""), reverse=True)
    return {"contract_id": contract_id, "checks": history, "total": len(history)}


@router.get("/jurisdictions", response_model=List[JurisdictionInfoResponse])
async def list_jurisdictions(current_user: dict = Depends(get_current_user)):
    """List all supported jurisdictions."""
    return [JurisdictionInfoResponse(**j) for j in JURISDICTIONS.values()]


@router.get("/jurisdictions/{code}", response_model=JurisdictionInfoResponse)
async def get_jurisdiction(
    code: str,
    current_user: dict = Depends(get_current_user),
):
    """Get information about a specific jurisdiction."""
    jurisdiction = JURISDICTIONS.get(code)
    if not jurisdiction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Jurisdiction '{code}' not found",
        )
    return JurisdictionInfoResponse(**jurisdiction)


@router.get("/frameworks")
async def list_frameworks(current_user: dict = Depends(get_current_user)):
    """List all supported compliance frameworks."""
    return {
        "frameworks": [
            {"id": "gdpr", "name": "General Data Protection Regulation", "region": "EU", "rules_count": 4},
            {"id": "hipaa", "name": "Health Insurance Portability and Accountability Act", "region": "US", "rules_count": 3},
            {"id": "sox", "name": "Sarbanes-Oxley Act", "region": "US", "rules_count": 2},
            {"id": "ccpa", "name": "California Consumer Privacy Act", "region": "US-CA", "rules_count": 2},
            {"id": "employment", "name": "Employment Law", "region": "Global", "rules_count": 3},
            {"id": "general", "name": "General Contract Law", "region": "Global", "rules_count": 7},
            {"id": "international", "name": "International Trade Law", "region": "Global", "rules_count": 2},
            {"id": "anti_corruption", "name": "Anti-Corruption / FCPA", "region": "US/Global", "rules_count": 1},
        ]
    }


@router.post("/report", response_model=ComplianceReportResponse)
async def generate_compliance_report(
    request: ComplianceReportRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate a comprehensive compliance report for a contract."""
    # Find latest compliance check for the contract
    checks = [
        c for c in _compliance_checks_db.values()
        if c.get("contract_id") == request.contract_id
    ]

    if not checks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No compliance checks found for this contract. Run a compliance check first.",
        )

    latest_check = max(checks, key=lambda c: c.get("checked_at", ""))

    report_id = str(uuid4())
    now = datetime.utcnow().isoformat()

    sections = []

    # Executive Summary Section
    sections.append({
        "title": "Executive Summary",
        "content": f"Overall compliance score: {latest_check['overall_score']:.1%}. "
                   f"Status: {latest_check['compliance_status']}. "
                   f"{latest_check['non_compliant_count']} non-compliant findings identified.",
    })

    # Framework Analysis
    for framework, score in latest_check.get("framework_scores", {}).items():
        framework_rules = [
            r for r in latest_check.get("rule_results", [])
            if r.get("framework") == framework
        ]
        sections.append({
            "title": f"Framework: {framework.upper()}",
            "score": score,
            "rules_checked": len(framework_rules),
            "findings": [
                r for r in framework_rules
                if r.get("status") != "compliant"
            ],
        })

    # Critical Violations
    if latest_check.get("critical_violations"):
        sections.append({
            "title": "Critical Violations",
            "violations": latest_check["critical_violations"],
            "requires_immediate_action": True,
        })

    # Recommendations
    sections.append({
        "title": "Recommendations",
        "items": latest_check.get("recommendations", []),
    })

    return ComplianceReportResponse(
        report_id=report_id,
        contract_id=request.contract_id,
        generated_at=now,
        format=request.format,
        overall_compliance_score=latest_check["overall_score"],
        sections=sections,
        executive_summary=(
            f"Compliance review completed for contract {request.contract_id}. "
            f"Overall score: {latest_check['overall_score']:.1%}. "
            f"Jurisdictions checked: {', '.join(latest_check.get('jurisdictions_checked', []))}. "
            f"Critical violations: {len(latest_check.get('critical_violations', []))}."
        ),
    )


@router.get("/updates", response_model=List[RegulatoryUpdateResponse])
async def get_regulatory_updates(
    framework: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """Get latest regulatory updates that may affect contracts."""
    updates = [
        RegulatoryUpdateResponse(
            id=str(uuid4()),
            framework="gdpr",
            jurisdiction="EU",
            title="GDPR AI Act Integration",
            description="New requirements for AI-generated contracts under the EU AI Act.",
            impact_level="high",
            effective_date="2025-08-01",
            published_date="2025-01-15",
            action_required=True,
        ),
        RegulatoryUpdateResponse(
            id=str(uuid4()),
            framework="ccpa",
            jurisdiction="US-CA",
            title="CPRA Amendments",
            description="Updated data processing requirements under CPRA amendments.",
            impact_level="medium",
            effective_date="2025-07-01",
            published_date="2025-02-01",
            action_required=True,
        ),
        RegulatoryUpdateResponse(
            id=str(uuid4()),
            framework="hipaa",
            jurisdiction="US-Federal",
            title="HIPAA Security Rule Update",
            description="Enhanced cybersecurity requirements for BAAs and covered entities.",
            impact_level="high",
            effective_date="2025-06-01",
            published_date="2025-01-20",
            action_required=True,
        ),
    ]

    if framework:
        updates = [u for u in updates if u.framework == framework]
    if jurisdiction:
        updates = [u for u in updates if u.jurisdiction == jurisdiction]

    return updates
