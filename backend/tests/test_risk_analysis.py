"""Tests for risk analysis service."""

import pytest
from app.services.risk_analyzer import RiskAnalyzer


@pytest.fixture
def risk_analyzer():
    return RiskAnalyzer()


@pytest.mark.asyncio
async def test_risk_analysis(risk_analyzer, sample_contract_content):
    """Test basic risk analysis."""
    result = await risk_analyzer.analyze(
        content=sample_contract_content,
        contract_type="nda",
        jurisdiction="US-Federal",
    )
    assert "overall_risk_score" in result
    assert "risk_factors" in result
    assert isinstance(result["risk_factors"], list)
    assert 0 <= result["overall_risk_score"] <= 1


@pytest.mark.asyncio
async def test_risk_analysis_categories(risk_analyzer, sample_contract_content):
    """Test that risk analysis covers multiple categories."""
    result = await risk_analyzer.analyze(
        content=sample_contract_content,
        contract_type="nda",
    )
    categories = set(f.get("category", "") for f in result["risk_factors"])
    # Should detect at least some categories
    assert len(categories) >= 1


@pytest.mark.asyncio
async def test_risk_analysis_empty_content(risk_analyzer):
    """Test risk analysis with empty content."""
    result = await risk_analyzer.analyze(content="", contract_type="general")
    assert "overall_risk_score" in result
    # Empty content should have higher risk (missing clauses)
    assert result["overall_risk_score"] > 0


@pytest.mark.asyncio
async def test_risk_analysis_high_risk(risk_analyzer):
    """Test that high-risk content is detected."""
    high_risk_content = """
    This agreement has unlimited liability for the receiving party.
    There is no limitation of liability clause.
    The agreement has no termination clause and runs indefinitely.
    No governing law is specified.
    No dispute resolution mechanism.
    """
    result = await risk_analyzer.analyze(content=high_risk_content, contract_type="general")
    assert result["overall_risk_score"] > 0.3


@pytest.mark.asyncio
async def test_executive_summary(risk_analyzer, sample_contract_content):
    """Test executive summary generation."""
    result = await risk_analyzer.analyze(
        content=sample_contract_content,
        contract_type="nda",
    )
    assert "executive_summary" in result
    assert len(result["executive_summary"]) > 0


@pytest.mark.asyncio
async def test_risk_api_endpoint(client, auth_headers, sample_contract_content):
    """Test risk analysis API endpoint."""
    from httpx import AsyncClient

    response = await client.post("/api/v1/review/risk-analysis", json={
        "content": sample_contract_content,
        "contract_type": "nda",
        "jurisdiction": "US-Federal",
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert "overall_risk_score" in data
    assert "risk_factors" in data
