"""
Contract Calendar & Deadlines API.
"""

from fastapi import APIRouter
from typing import Optional
from datetime import datetime, timedelta
import uuid
import random

router = APIRouter(prefix="/calendar", tags=["Calendar"])


# ── Seed calendar events ────────────────────────────────────────────

def _seed_events() -> list[dict]:
    """Generate realistic calendar events."""
    now = datetime.utcnow()
    event_templates = [
        # Past/overdue events
        {"title": "IP Assignment Agreement — Review Due", "type": "review_due", "color": "red", "contract_type": "IP Assignment", "offset_days": -5},
        {"title": "Vendor Contract — Payment Deadline", "type": "payment", "color": "red", "contract_type": "Vendor", "offset_days": -2},
        # Today
        {"title": "NDA — Annual Review", "type": "review_due", "color": "yellow", "contract_type": "NDA", "offset_days": 0},
        # Upcoming (this week)
        {"title": "Employment Agreement — Probation End", "type": "milestone", "color": "blue", "contract_type": "Employment", "offset_days": 2},
        {"title": "SaaS License — Renewal Decision", "type": "renewal", "color": "yellow", "contract_type": "SaaS", "offset_days": 4},
        {"title": "Service Agreement — Compliance Audit", "type": "compliance", "color": "purple", "contract_type": "Service", "offset_days": 5},
        # Next week
        {"title": "Consulting Agreement — Deliverable Due", "type": "milestone", "color": "blue", "contract_type": "Consulting", "offset_days": 8},
        {"title": "NDA — Expiry Notice Required", "type": "expiry", "color": "orange", "contract_type": "NDA", "offset_days": 10},
        {"title": "MSA — Quarterly Review", "type": "review_due", "color": "blue", "contract_type": "MSA", "offset_days": 12},
        # This month
        {"title": "Data Processing Agreement — GDPR Audit", "type": "compliance", "color": "purple", "contract_type": "DPA", "offset_days": 15},
        {"title": "Licensing Agreement — Royalty Payment", "type": "payment", "color": "green", "contract_type": "Licensing", "offset_days": 18},
        {"title": "Supply Agreement — Contract Renewal", "type": "renewal", "color": "yellow", "contract_type": "Supply", "offset_days": 20},
        {"title": "Joint Venture — Board Approval Deadline", "type": "milestone", "color": "blue", "contract_type": "Joint Venture", "offset_days": 22},
        {"title": "Employment Contract — Benefits Review", "type": "review_due", "color": "blue", "contract_type": "Employment", "offset_days": 25},
        {"title": "SaaS Agreement — SLA Review", "type": "review_due", "color": "blue", "contract_type": "SaaS", "offset_days": 27},
        # Next month
        {"title": "Master Service Agreement — Annual Renewal", "type": "renewal", "color": "yellow", "contract_type": "MSA", "offset_days": 35},
        {"title": "NDA — Expiry", "type": "expiry", "color": "orange", "contract_type": "NDA", "offset_days": 40},
        {"title": "Vendor Agreement — Performance Review", "type": "review_due", "color": "blue", "contract_type": "Vendor", "offset_days": 42},
        {"title": "Insurance Policy — Renewal Deadline", "type": "renewal", "color": "yellow", "contract_type": "Insurance", "offset_days": 50},
        {"title": "Partnership Agreement — Profit Distribution", "type": "payment", "color": "green", "contract_type": "Partnership", "offset_days": 55},
        {"title": "Lease Agreement — Option Exercise Deadline", "type": "milestone", "color": "red", "contract_type": "Lease", "offset_days": 60},
        {"title": "Technology License — Compliance Check", "type": "compliance", "color": "purple", "contract_type": "Licensing", "offset_days": 65},
    ]

    events = []
    for tmpl in event_templates:
        event_date = now + timedelta(days=tmpl["offset_days"])
        is_overdue = tmpl["offset_days"] < 0
        events.append({
            "id": str(uuid.uuid4())[:8],
            "title": tmpl["title"],
            "date": event_date.strftime("%Y-%m-%d"),
            "time": f"{random.randint(9, 17):02d}:00",
            "type": tmpl["type"],
            "color": "red" if is_overdue else tmpl["color"],
            "contract_type": tmpl["contract_type"],
            "is_overdue": is_overdue,
            "is_today": tmpl["offset_days"] == 0,
            "days_until": tmpl["offset_days"],
            "priority": "high" if is_overdue or tmpl["offset_days"] <= 3 else "medium" if tmpl["offset_days"] <= 14 else "low",
            "contract_id": f"contract-{random.randint(100, 999)}",
        })

    return sorted(events, key=lambda e: e["date"])


_events = _seed_events()


@router.get("/events")
async def get_events(
    month: Optional[int] = None,
    year: Optional[int] = None,
    event_type: Optional[str] = None,
):
    """Get calendar events, optionally filtered by month/year."""
    filtered = _events

    if month and year:
        filtered = [
            e for e in filtered
            if datetime.strptime(e["date"], "%Y-%m-%d").month == month
            and datetime.strptime(e["date"], "%Y-%m-%d").year == year
        ]
    elif year:
        filtered = [e for e in filtered if datetime.strptime(e["date"], "%Y-%m-%d").year == year]

    if event_type:
        filtered = [e for e in filtered if e["type"] == event_type]

    # Build summary
    type_counts = {}
    for e in filtered:
        type_counts[e["type"]] = type_counts.get(e["type"], 0) + 1

    overdue = [e for e in filtered if e["is_overdue"]]

    return {
        "events": filtered,
        "total": len(filtered),
        "overdue_count": len(overdue),
        "type_summary": type_counts,
    }


@router.get("/upcoming")
async def get_upcoming(days: int = 30):
    """Get upcoming events within the next N days."""
    now = datetime.utcnow()
    cutoff = now + timedelta(days=days)

    upcoming = [
        e for e in _events
        if now.strftime("%Y-%m-%d") <= e["date"] <= cutoff.strftime("%Y-%m-%d")
    ]

    # Group by priority
    high = [e for e in upcoming if e["priority"] == "high"]
    medium = [e for e in upcoming if e["priority"] == "medium"]
    low = [e for e in upcoming if e["priority"] == "low"]

    return {
        "upcoming": upcoming,
        "total": len(upcoming),
        "by_priority": {
            "high": len(high),
            "medium": len(medium),
            "low": len(low),
        },
        "overdue": [e for e in _events if e["is_overdue"]],
    }


@router.get("/event-types")
async def get_event_types():
    """List available event types."""
    return {
        "types": [
            {"id": "review_due", "label": "Review Due", "color": "blue", "icon": "📋"},
            {"id": "renewal", "label": "Renewal", "color": "yellow", "icon": "🔄"},
            {"id": "expiry", "label": "Expiry", "color": "orange", "icon": "⏰"},
            {"id": "compliance", "label": "Compliance", "color": "purple", "icon": "🛡️"},
            {"id": "payment", "label": "Payment", "color": "green", "icon": "💰"},
            {"id": "milestone", "label": "Milestone", "color": "blue", "icon": "🎯"},
        ]
    }
