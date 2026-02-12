"""Tests for contract generation and management."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_generate_contract(client: AsyncClient, auth_headers):
    """Test contract generation."""
    response = await client.post("/api/v1/contracts/generate", json={
        "contract_type": "nda",
        "title": "Test NDA",
        "parties": [
            {"name": "Company A", "role": "Disclosing Party"},
            {"name": "Company B", "role": "Receiving Party"},
        ],
        "jurisdiction": "US-Federal",
        "variables": {
            "effective_date": "2025-01-01",
            "term_years": "2",
            "governing_state": "Delaware",
        },
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test NDA"
    assert data["contract_type"] == "nda"
    assert data["status"] == "draft"
    assert len(data["content"]) > 0
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_list_contracts(client: AsyncClient, auth_headers):
    """Test listing contracts."""
    # Generate a contract first
    await client.post("/api/v1/contracts/generate", json={
        "contract_type": "nda",
        "title": "List Test NDA",
        "parties": [
            {"name": "A", "role": "Party A"},
            {"name": "B", "role": "Party B"},
        ],
    }, headers=auth_headers)

    response = await client.get("/api/v1/contracts/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "contracts" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.asyncio
async def test_get_contract(client: AsyncClient, auth_headers):
    """Test getting a specific contract."""
    # Create contract
    gen_response = await client.post("/api/v1/contracts/generate", json={
        "contract_type": "msa",
        "title": "Test MSA",
        "parties": [
            {"name": "Client", "role": "Client"},
            {"name": "Provider", "role": "Service Provider"},
        ],
    }, headers=auth_headers)
    contract_id = gen_response.json()["id"]

    # Get it
    response = await client.get(f"/api/v1/contracts/{contract_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == contract_id


@pytest.mark.asyncio
async def test_update_contract(client: AsyncClient, auth_headers):
    """Test updating a contract."""
    gen_response = await client.post("/api/v1/contracts/generate", json={
        "contract_type": "nda",
        "title": "Update Test",
        "parties": [{"name": "A", "role": "A"}, {"name": "B", "role": "B"}],
    }, headers=auth_headers)
    contract_id = gen_response.json()["id"]

    response = await client.put(f"/api/v1/contracts/{contract_id}", json={
        "title": "Updated Title",
        "status": "in_review",
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    assert response.json()["status"] == "in_review"


@pytest.mark.asyncio
async def test_contract_not_found(client: AsyncClient, auth_headers):
    """Test getting non-existent contract."""
    response = await client.get("/api/v1/contracts/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_templates(client: AsyncClient, auth_headers):
    """Test listing contract templates."""
    response = await client.get("/api/v1/contracts/templates", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "templates" in data
    assert len(data["templates"]) > 0


@pytest.mark.asyncio
async def test_explain_clause(client: AsyncClient, auth_headers):
    """Test clause explanation."""
    response = await client.post("/api/v1/contracts/explain-clause", json={
        "clause_text": "The Receiving Party shall indemnify and hold harmless the Disclosing Party.",
        "audience": "business",
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "plain_language" in data
    assert "legal_implications" in data
    assert "risk_factors" in data
