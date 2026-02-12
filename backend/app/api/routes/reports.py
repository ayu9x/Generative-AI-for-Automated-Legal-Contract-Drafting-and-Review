"""
Reports & Analytics API — Portfolio analytics and contract export.
"""

from fastapi import APIRouter
from typing import Optional
from datetime import datetime, timedelta
import random
import uuid

router = APIRouter(prefix="/reports", tags=["Reports"])


# ── Analytics data generators ───────────────────────────────────────

def _generate_monthly_data() -> list[dict]:
    """Generate 12 months of contract volume data."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    data = []
    for i, month in enumerate(months):
        base = random.randint(8, 25)
        data.append({
            "month": month,
            "contracts_created": base,
            "contracts_reviewed": int(base * random.uniform(0.6, 0.9)),
            "contracts_approved": int(base * random.uniform(0.4, 0.7)),
            "high_risk_count": int(base * random.uniform(0.1, 0.3)),
        })
    return data


def _generate_type_distribution() -> list[dict]:
    """Generate contract type distribution."""
    types = [
        {"type": "NDA", "count": 45, "percentage": 22.5},
        {"type": "Employment", "count": 38, "percentage": 19.0},
        {"type": "SaaS Agreement", "count": 32, "percentage": 16.0},
        {"type": "Service Agreement", "count": 28, "percentage": 14.0},
        {"type": "Consulting", "count": 20, "percentage": 10.0},
        {"type": "Licensing", "count": 15, "percentage": 7.5},
        {"type": "M&A", "count": 12, "percentage": 6.0},
        {"type": "Other", "count": 10, "percentage": 5.0},
    ]
    return types


def _generate_compliance_data() -> dict:
    """Generate compliance statistics."""
    return {
        "frameworks": [
            {"name": "GDPR", "total_checks": 156, "passed": 138, "failed": 12, "pending": 6, "pass_rate": 88.5},
            {"name": "HIPAA", "total_checks": 89, "passed": 72, "failed": 10, "pending": 7, "pass_rate": 80.9},
            {"name": "SOX", "total_checks": 67, "passed": 58, "failed": 5, "pending": 4, "pass_rate": 86.6},
            {"name": "PCI-DSS", "total_checks": 43, "passed": 39, "failed": 2, "pending": 2, "pass_rate": 90.7},
            {"name": "CCPA", "total_checks": 78, "passed": 68, "failed": 7, "pending": 3, "pass_rate": 87.2},
        ],
        "overall_pass_rate": 86.8,
        "total_checks": 433,
    }


def _generate_risk_trends() -> list[dict]:
    """Generate risk trend data for last 6 months."""
    months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    data = []
    for month in months:
        total = random.randint(15, 30)
        high = int(total * random.uniform(0.1, 0.25))
        medium = int(total * random.uniform(0.25, 0.4))
        low = total - high - medium
        data.append({
            "month": month,
            "high_risk": high,
            "medium_risk": medium,
            "low_risk": low,
            "total": total,
        })
    return data


@router.get("/analytics")
async def get_analytics():
    """Get comprehensive portfolio analytics."""
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "period": "Last 12 months",
        "monthly_volume": _generate_monthly_data(),
        "type_distribution": _generate_type_distribution(),
        "compliance": _generate_compliance_data(),
        "risk_trends": _generate_risk_trends(),
        "key_metrics": {
            "total_contracts": 200,
            "active_contracts": 142,
            "expired_contracts": 38,
            "pending_review": 20,
            "average_processing_time_hours": 4.2,
            "average_risk_score": 0.42,
            "compliance_rate": 86.8,
            "contracts_this_month": 18,
            "growth_rate_percent": 12.5,
        },
    }


@router.get("/export/{contract_id}")
async def export_contract(contract_id: str, format: str = "json"):
    """Generate export data for a contract."""
    # Demo export data
    export_data = {
        "export_id": str(uuid.uuid4())[:8],
        "contract_id": contract_id,
        "format": format,
        "generated_at": datetime.utcnow().isoformat(),
        "content": {
            "title": f"Contract {contract_id}",
            "type": "Non-Disclosure Agreement",
            "status": "approved",
            "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat(),
            "parties": ["Party A (Disclosing Party)", "Party B (Receiving Party)"],
            "jurisdiction": "United States — Delaware",
            "key_terms": {
                "confidentiality_period": "3 years",
                "governing_law": "Delaware",
                "dispute_resolution": "Arbitration (AAA Rules)",
                "termination_notice": "30 days written notice",
            },
            "risk_summary": {
                "overall_risk": "medium",
                "risk_score": 0.45,
                "flags": ["Broad definition of confidential information", "No mutual obligations"],
            },
            "compliance": {
                "gdpr": "passed",
                "hipaa": "not_applicable",
                "sox": "passed",
            },
        },
    }
    return export_data


@router.get("/summary")
async def get_portfolio_summary():
    """High-level portfolio summary for reports page."""
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "totals": {
            "all_time_contracts": 200,
            "this_month": 18,
            "this_week": 5,
            "today": 2,
        },
        "by_status": [
            {"status": "draft", "count": 25, "percentage": 12.5},
            {"status": "in_review", "count": 20, "percentage": 10.0},
            {"status": "approved", "count": 120, "percentage": 60.0},
            {"status": "rejected", "count": 15, "percentage": 7.5},
            {"status": "expired", "count": 20, "percentage": 10.0},
        ],
        "by_jurisdiction": [
            {"jurisdiction": "United States", "count": 95, "percentage": 47.5},
            {"jurisdiction": "European Union", "count": 48, "percentage": 24.0},
            {"jurisdiction": "United Kingdom", "count": 30, "percentage": 15.0},
            {"jurisdiction": "International", "count": 27, "percentage": 13.5},
        ],
        "top_creators": [
            {"name": "Admin User", "count": 85},
            {"name": "Jane Smith", "count": 52},
            {"name": "John Doe", "count": 38},
            {"name": "Sarah Wilson", "count": 25},
        ],
    }
