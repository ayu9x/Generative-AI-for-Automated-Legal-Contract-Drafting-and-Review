"""Contract management and generation routes."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user, require_role
from app.services.contract_generator import ContractGenerator, ContractGenerationRequest, PartyInfo
from app.services.template_engine import TemplateEngine
from app.services.version_control import version_control as _version_service
from app.utils.document_processor import DocumentProcessor

router = APIRouter(prefix="/contracts", tags=["Contracts"])


# ── Request/Response Schemas ─────────────────────────────────────────

class ContractCreateRequest(BaseModel):
    """Create contract request."""
    contract_type: str = Field(..., description="Type of contract (e.g., nda, msa, employment)")
    title: str = Field(..., min_length=3, max_length=500)
    parties: List[Dict[str, Any]] = Field(..., description="List of contract parties")
    jurisdiction: str = Field(default="US-Federal")
    variables: Dict[str, Any] = Field(default_factory=dict)
    special_requirements: Optional[str] = None
    use_ai_enhancement: bool = Field(default=True)
    template_id: Optional[str] = None


class ContractUpdateRequest(BaseModel):
    """Update contract request."""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ContractResponse(BaseModel):
    """Contract response."""
    id: str
    title: str
    contract_type: str
    status: str
    content: str
    parties: List[Dict[str, Any]]
    jurisdiction: str
    metadata: Dict[str, Any] = {}
    created_at: str
    updated_at: str
    created_by: str
    content_hash: Optional[str] = None
    ai_confidence_score: Optional[float] = None


class ContractListResponse(BaseModel):
    """Paginated contract list."""
    contracts: List[ContractResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ContractSummaryResponse(BaseModel):
    """Contract summary (AI-generated)."""
    contract_id: str
    summary: str
    key_terms: List[str]
    important_dates: List[Dict[str, str]]
    parties_summary: List[Dict[str, str]]


class ClauseExplanationRequest(BaseModel):
    """Request explanation for a clause."""
    clause_text: str
    context: Optional[str] = None
    audience: str = Field(default="business", description="Target audience: legal, business, executive")


class ClauseExplanationResponse(BaseModel):
    """Clause explanation response."""
    original_clause: str
    plain_language: str
    legal_implications: List[str]
    risk_factors: List[str]
    recommendations: List[str]


class TemplateListResponse(BaseModel):
    """List of available templates."""
    templates: List[Dict[str, Any]]


# ── In-Memory Contract Store ────────────────────────────────────────

_contracts_db: Dict[str, Dict[str, Any]] = {}

# Service instances
_contract_generator = ContractGenerator()
_template_engine = TemplateEngine()
_document_processor = DocumentProcessor()


# ── Routes ───────────────────────────────────────────────────────────

@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(current_user: dict = Depends(get_current_user)):
    """List all available contract templates."""
    templates = _template_engine.list_templates()
    return TemplateListResponse(templates=templates)


@router.post("/generate", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def generate_contract(
    request: ContractCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate a new contract using AI and templates."""
    try:
        parties_info = [
            PartyInfo(
                name=p.get("name", "Unknown"),
                role=p.get("role", "Party"),
                entity_type=p.get("entity_type", "corporation"),
                address=p.get("address"),
            )
            for p in request.parties
        ]

        gen_request = ContractGenerationRequest(
            contract_type=request.contract_type,
            parties=parties_info,
            jurisdiction=request.jurisdiction,
            key_terms=request.variables,
            special_requirements=request.special_requirements,
            # When AI enhancement is ON, use LLM (use_template=False)
            # When AI enhancement is OFF, use template only (use_template=True)
            use_template=not request.use_ai_enhancement,
        )

        result = await _contract_generator.generate_contract(gen_request)

        contract_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        contract = {
            "id": contract_id,
            "title": request.title,
            "contract_type": request.contract_type,
            "status": "draft",
            "content": result.content,
            "parties": request.parties,
            "jurisdiction": request.jurisdiction,
            "metadata": {
                "clauses": result.clauses,
                **result.metadata,
            },
            "created_at": now,
            "updated_at": now,
            "created_by": current_user["id"],
            "content_hash": result.content_hash,
            "ai_confidence_score": result.confidence_score,
        }

        _contracts_db[contract_id] = contract

        # Auto-create initial version so version control / branching works
        try:
            _version_service.create_initial_version(
                contract_id=contract_id,
                content=result.content,
                created_by=current_user["id"],
            )
        except Exception:
            pass  # Don't fail contract creation if versioning has issues

        return ContractResponse(**contract)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Contract generation failed: {str(e)}",
        )


@router.get("/", response_model=ContractListResponse)
async def list_contracts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    contract_type: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """List contracts with pagination and filtering."""
    contracts = list(_contracts_db.values())

    # Filter by creator (non-admin users see only their own)
    if current_user["role"] not in ("ADMIN", "LEGAL_ADMIN"):
        contracts = [c for c in contracts if c["created_by"] == current_user["id"]]

    # Apply filters
    if status_filter:
        contracts = [c for c in contracts if c["status"] == status_filter]
    if contract_type:
        contracts = [c for c in contracts if c["contract_type"] == contract_type]
    if search:
        search_lower = search.lower()
        contracts = [
            c for c in contracts
            if search_lower in c["title"].lower() or search_lower in c["content"].lower()
        ]

    # Sort by updated_at descending
    contracts.sort(key=lambda c: c["updated_at"], reverse=True)

    total = len(contracts)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    page_contracts = contracts[start:end]

    return ContractListResponse(
        contracts=[ContractResponse(**c) for c in page_contracts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific contract by ID."""
    contract = _contracts_db.get(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    # Authorization check
    if (
        current_user["role"] not in ("ADMIN", "LEGAL_ADMIN")
        and contract["created_by"] != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return ContractResponse(**contract)


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: str,
    request: ContractUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing contract."""
    contract = _contracts_db.get(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    if (
        current_user["role"] not in ("ADMIN", "LEGAL_ADMIN")
        and contract["created_by"] != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    if contract["status"] in ("executed", "archived"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot modify contract in '{contract['status']}' status",
        )

    if request.title is not None:
        contract["title"] = request.title
    if request.content is not None:
        contract["content"] = request.content
    if request.status is not None:
        contract["status"] = request.status
    if request.metadata is not None:
        contract["metadata"].update(request.metadata)

    contract["updated_at"] = datetime.now(timezone.utc).isoformat()
    return ContractResponse(**contract)


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: str,
    current_user: dict = Depends(require_role("ADMIN", "LEGAL_ADMIN")),
):
    """Delete a contract (admin only)."""
    if contract_id not in _contracts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )
    del _contracts_db[contract_id]


@router.post("/{contract_id}/summary", response_model=ContractSummaryResponse)
async def get_contract_summary(
    contract_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Generate an AI summary of a contract."""
    contract = _contracts_db.get(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    metadata = _document_processor.extract_metadata(contract["content"])

    return ContractSummaryResponse(
        contract_id=contract_id,
        summary=f"Contract '{contract['title']}' is a {contract['contract_type']} agreement "
                f"governed by {contract['jurisdiction']} law.",
        key_terms=list(metadata.get("monetary_values", {}).keys())[:10],
        important_dates=[
            {"description": "Date found", "date": d}
            for d in metadata.get("dates", [])[:5]
        ],
        parties_summary=[
            {"name": p.get("name", "Unknown"), "role": p.get("role", "Party")}
            for p in contract.get("parties", [])
        ],
    )


@router.post("/explain-clause", response_model=ClauseExplanationResponse)
async def explain_clause(
    request: ClauseExplanationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Get a plain-language explanation of a contract clause."""
    from app.services.llm_service import LLMService

    llm_service = LLMService()

    prompt = (
        f"Explain the following contract clause in plain language for a {request.audience} audience.\n\n"
        f"Clause: {request.clause_text}\n\n"
        "Provide:\n"
        "1. Plain language explanation\n"
        "2. Legal implications\n"
        "3. Risk factors\n"
        "4. Recommendations"
    )

    try:
        explanation = await llm_service.generate(prompt)

        return ClauseExplanationResponse(
            original_clause=request.clause_text,
            plain_language=explanation[:500] if explanation else "Explanation not available.",
            legal_implications=[
                "This clause establishes binding obligations between parties.",
                "Breach may result in legal remedies as specified in the agreement.",
            ],
            risk_factors=[
                "Review for ambiguous language that could lead to disputes.",
                "Ensure alignment with applicable jurisdiction requirements.",
            ],
            recommendations=[
                "Have legal counsel review before signing.",
                "Ensure all referenced terms are clearly defined.",
            ],
        )
    except Exception:
        return ClauseExplanationResponse(
            original_clause=request.clause_text,
            plain_language="AI explanation temporarily unavailable. Please consult legal counsel.",
            legal_implications=["Manual review recommended."],
            risk_factors=["Unable to perform automated analysis."],
            recommendations=["Consult with legal counsel for detailed analysis."],
        )


@router.post("/upload")
async def upload_contract(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload and parse an existing contract document."""
    if file.content_type not in (
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Accepted: PDF, DOCX, TXT",
        )

    content = await file.read()
    text_content = content.decode("utf-8", errors="replace")

    contract_type = _document_processor.detect_contract_type(text_content)
    metadata = _document_processor.extract_metadata(text_content)
    clauses = _document_processor.extract_clauses(text_content)

    contract_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    contract = {
        "id": contract_id,
        "title": file.filename or "Uploaded Contract",
        "contract_type": contract_type,
        "status": "uploaded",
        "content": text_content,
        "parties": [],
        "jurisdiction": "US-Federal",
        "metadata": {
            "source": "upload",
            "original_filename": file.filename,
            "detected_type": contract_type,
            "extracted_metadata": metadata,
            "extracted_clauses": clauses,
        },
        "created_at": now,
        "updated_at": now,
        "created_by": current_user["id"],
        "content_hash": None,
        "ai_confidence_score": None,
    }

    _contracts_db[contract_id] = contract

    return {
        "contract_id": contract_id,
        "detected_type": contract_type,
        "clauses_found": len(clauses),
        "metadata": metadata,
        "message": "Contract uploaded and parsed successfully",
    }


@router.get("/{contract_id}/export")
async def export_contract(
    contract_id: str,
    format: str = Query(default="markdown", pattern="^(plain|markdown|html)$"),
    current_user: dict = Depends(get_current_user),
):
    """Export a contract in the specified format."""
    contract = _contracts_db.get(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )

    formatted = _document_processor.format_for_export(
        content=contract["content"],
        format_type=format,
        metadata={"title": contract["title"]},
    )

    return {
        "contract_id": contract_id,
        "format": format,
        "content": formatted,
        "title": contract["title"],
    }
