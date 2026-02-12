"""Tests for compliance checking service."""

import pytest
from app.services.compliance_checker import ComplianceChecker


@pytest.fixture
def compliance_checker():
    return ComplianceChecker()


@pytest.mark.asyncio
async def test_compliance_check(compliance_checker, sample_contract_content):
    """Test basic compliance check."""
    result = await compliance_checker.check_compliance(
        content=sample_contract_content,
        contract_type="nda",
        jurisdictions=["US-Federal"],
        frameworks=["general"],
    )
    assert "overall_score" in result
    assert "rule_results" in result
    assert isinstance(result["rule_results"], list)
    assert 0 <= result["overall_score"] <= 1


@pytest.mark.asyncio
async def test_gdpr_compliance(compliance_checker):
    """Test GDPR-specific compliance checks."""
    gdpr_content = """
    This agreement includes data processing provisions.
    Personal data shall be processed in accordance with applicable data protection laws.
    The data processor shall implement appropriate technical and organizational measures.
    Data subjects have the right to access, rectify, and erase their personal data.
    Data shall not be transferred outside the EU without adequate safeguards.
    """
    result = await compliance_checker.check_compliance(
        content=gdpr_content,
        contract_type="service_agreement",
        jurisdictions=["EU"],
        frameworks=["gdpr"],
    )
    assert "overall_score" in result
    gdpr_rules = [r for r in result["rule_results"] if r.get("framework") == "gdpr"]
    assert len(gdpr_rules) > 0


@pytest.mark.asyncio
async def test_hipaa_compliance(compliance_checker):
    """Test HIPAA-specific compliance checks."""
    hipaa_content = """
    This Business Associate Agreement governs the use of Protected Health Information (PHI).
    The Business Associate agrees to safeguard PHI in accordance with HIPAA regulations.
    Security measures include encryption, access controls, and audit trails.
    Breach notification shall occur within 60 days of discovery.
    """
    result = await compliance_checker.check_compliance(
        content=hipaa_content,
        contract_type="service_agreement",
        jurisdictions=["US-Federal"],
        frameworks=["hipaa"],
    )
    assert "overall_score" in result
    hipaa_rules = [r for r in result["rule_results"] if r.get("framework") == "hipaa"]
    assert len(hipaa_rules) > 0


@pytest.mark.asyncio
async def test_multi_framework_compliance(compliance_checker, sample_contract_content):
    """Test compliance check across multiple frameworks."""
    result = await compliance_checker.check_compliance(
        content=sample_contract_content,
        contract_type="nda",
        jurisdictions=["US-Federal", "EU"],
        frameworks=["general", "gdpr"],
    )
    assert "overall_score" in result
    assert "framework_scores" in result
    assert len(result["rule_results"]) > 0


@pytest.mark.asyncio
async def test_compliance_recommendations(compliance_checker, sample_contract_content):
    """Test that compliance check provides recommendations."""
    result = await compliance_checker.check_compliance(
        content=sample_contract_content,
        contract_type="nda",
        frameworks=["general"],
    )
    assert "recommendations" in result


@pytest.mark.asyncio
async def test_compliance_api_endpoint(client, auth_headers, sample_contract_content):
    """Test compliance API endpoint."""
    from httpx import AsyncClient

    response = await client.post("/api/v1/compliance/check", json={
        "content": sample_contract_content,
        "contract_type": "nda",
        "jurisdictions": ["US-Federal"],
        "frameworks": ["general"],
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "check_id" in data
    assert "overall_score" in data
    assert "rule_results" in data


@pytest.mark.asyncio
async def test_list_jurisdictions(client, auth_headers):
    """Test listing jurisdictions."""
    response = await client.get("/api/v1/compliance/jurisdictions", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_frameworks(client, auth_headers):
    """Test listing compliance frameworks."""
    response = await client.get("/api/v1/compliance/frameworks", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "frameworks" in data
