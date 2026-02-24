"""Web Search API routes for legal research."""

from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.routes.auth import get_current_user
from app.services.web_search_service import web_search_service

router = APIRouter(prefix="/search", tags=["Web Search"])


# ─── Request/Response Schemas ───────────────────────────────────────────


class LegalSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    jurisdiction: str = Field(default="US")
    num_results: int = Field(default=5, ge=1, le=10)


class ComplianceSearchRequest(BaseModel):
    regulation: str = Field(..., min_length=2, max_length=200)
    jurisdiction: str = Field(default="US")


class CaseLawSearchRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500)
    jurisdiction: str = Field(default="US")


class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str
    source: str


class LegalSearchResponse(BaseModel):
    query: str
    jurisdiction: str
    results: List[SearchResult]
    result_count: int


class ComplianceSearchResponse(BaseModel):
    regulation: str
    jurisdiction: str
    updates: List[SearchResult]
    update_count: int


class CaseLawSearchResponse(BaseModel):
    topic: str
    jurisdiction: str
    cases: List[SearchResult]
    case_count: int


# ─── Endpoints ──────────────────────────────────────────────────────────


@router.post("/legal", response_model=LegalSearchResponse)
async def search_legal_info(
    request: LegalSearchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Search the internet for legal information, regulations, and precedents."""
    try:
        result = await web_search_service.search_legal_info(
            query=request.query,
            jurisdiction=request.jurisdiction,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post("/regulations", response_model=ComplianceSearchResponse)
async def search_compliance_updates(
    request: ComplianceSearchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Search for latest regulatory and compliance updates."""
    try:
        result = await web_search_service.search_compliance_updates(
            regulation=request.regulation,
            jurisdiction=request.jurisdiction,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post("/case-law", response_model=CaseLawSearchResponse)
async def search_case_law(
    request: CaseLawSearchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Search for relevant case law and legal precedents."""
    try:
        result = await web_search_service.search_case_law(
            topic=request.topic,
            jurisdiction=request.jurisdiction,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/status")
async def get_search_status(
    current_user: dict = Depends(get_current_user),
):
    """Check web search service status and configuration."""
    return {
        "enabled": web_search_service.enabled,
        "google_configured": web_search_service.google_configured,
        "fallback_available": True,  # DuckDuckGo is always available
        "max_results": web_search_service.max_results,
    }
