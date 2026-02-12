"""Test configuration and fixtures."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest_asyncio.fixture
async def client():
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_contract_content():
    """Sample contract text for testing."""
    return """
    NON-DISCLOSURE AGREEMENT

    This Non-Disclosure Agreement ("Agreement") is entered into as of January 1, 2025
    ("Effective Date"), by and between:

    Company A, a Delaware corporation ("Disclosing Party"), and
    Company B, a California corporation ("Receiving Party").

    1. DEFINITIONS
    "Confidential Information" means any non-public information disclosed by the Disclosing
    Party to the Receiving Party, including but not limited to trade secrets, business plans,
    financial data, customer lists, and technical information.

    2. OBLIGATIONS
    The Receiving Party agrees to:
    (a) Hold Confidential Information in strict confidence;
    (b) Not disclose Confidential Information to any third party without prior written consent;
    (c) Use Confidential Information solely for the purposes of evaluating the potential business
        relationship between the parties.

    3. TERM AND TERMINATION
    This Agreement shall remain in effect for a period of two (2) years from the Effective Date.
    The confidentiality obligations shall survive termination for a period of five (5) years.

    4. GOVERNING LAW
    This Agreement shall be governed by and construed in accordance with the laws of the
    State of Delaware, without regard to its conflict of laws principles.

    5. INDEMNIFICATION
    The Receiving Party shall indemnify and hold harmless the Disclosing Party from any
    damages, losses, or expenses arising from any breach of this Agreement.

    6. LIMITATION OF LIABILITY
    Neither party shall be liable for any indirect, incidental, special, or consequential damages.
    The total liability under this Agreement shall not exceed $1,000,000.

    7. DISPUTE RESOLUTION
    Any disputes arising under this Agreement shall be resolved through binding arbitration
    in accordance with the rules of the American Arbitration Association.

    IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above.
    """


@pytest.fixture
def sample_parties():
    """Sample contract parties."""
    return [
        {"name": "Test Corp", "role": "Disclosing Party"},
        {"name": "Acme Inc", "role": "Receiving Party"},
    ]


@pytest.fixture
def auth_headers():
    """Get auth headers for testing."""
    from app.core.security import create_access_token
    token = create_access_token({"sub": "test-user-id", "email": "test@example.com", "role": "ADMIN"})
    return {"Authorization": f"Bearer {token}"}
