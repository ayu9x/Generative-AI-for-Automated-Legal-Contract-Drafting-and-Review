"""Audit log viewing routes (admin-only)."""

from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.routes.auth import get_current_user, require_role

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


# ── In-Memory Audit Log Store ───────────────────────────────────────

_audit_logs: list = []

# Seed demo audit entries
_demo_actions = [
    ("LOGIN", "auth", "User logged in successfully"),
    ("CONTRACT_CREATE", "contracts", "Generated NDA contract"),
    ("CONTRACT_VIEW", "contracts", "Viewed contract details"),
    ("RISK_ANALYSIS", "review", "Ran risk analysis on contract"),
    ("COMPLIANCE_CHECK", "compliance", "Checked GDPR compliance"),
    ("CONTRACT_UPDATE", "contracts", "Updated contract content"),
    ("CONTRACT_EXPORT", "contracts", "Exported contract as PDF"),
    ("VERSION_CREATE", "versions", "Created new version v1.1"),
    ("PROFILE_UPDATE", "auth", "Updated user profile"),
    ("PASSWORD_CHANGE", "auth", "Changed account password"),
    ("LOGIN", "auth", "User logged in successfully"),
    ("CONTRACT_CREATE", "contracts", "Generated Employment contract"),
    ("RISK_ANALYSIS", "review", "Ran risk analysis on contract"),
    ("COMPLIANCE_CHECK", "compliance", "Checked HIPAA compliance"),
    ("CONTRACT_APPROVE", "contracts", "Approved contract for signing"),
    ("VERSION_MERGE", "versions", "Merged branch edits into main"),
    ("CONTRACT_CREATE", "contracts", "Generated MSA contract"),
    ("CONTRACT_DELETE", "contracts", "Deleted draft contract"),
    ("API_KEY_CREATE", "auth", "Generated new API key"),
    ("TEMPLATE_VIEW", "templates", "Viewed NDA template"),
    ("LOGIN", "auth", "User logged in from new device"),
    ("CONTRACT_CREATE", "contracts", "Generated SaaS Agreement"),
    ("COMPLIANCE_CHECK", "compliance", "Checked SOX compliance"),
    ("RISK_ANALYSIS", "review", "Ran risk analysis — high risk detected"),
    ("CONTRACT_VIEW", "contracts", "Viewed contract details"),
]

_now = datetime.now(timezone.utc)
for i, (action, resource, description) in enumerate(_demo_actions):
    _audit_logs.append({
        "id": str(uuid4()),
        "timestamp": (_now - timedelta(hours=i * 2, minutes=i * 7)).isoformat(),
        "user_id": "demo-admin-001",
        "user_email": "admin@legalai.com",
        "action": action,
        "resource": resource,
        "description": description,
        "ip_address": "127.0.0.1",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "status": "success",
        "metadata": {},
    })


def record_audit(user_id: str, user_email: str, action: str, resource: str, description: str, ip: str = "127.0.0.1"):
    """Record a new audit log entry (call from other routes)."""
    _audit_logs.insert(0, {
        "id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "user_email": user_email,
        "action": action,
        "resource": resource,
        "description": description,
        "ip_address": ip,
        "user_agent": "",
        "status": "success",
        "metadata": {},
    })


# ── Routes ───────────────────────────────────────────────────────────

@router.get("/logs")
async def list_audit_logs(
    action: Optional[str] = None,
    resource: Optional[str] = None,
    user_email: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(require_role("ADMIN", "LEGAL_ADMIN")),
):
    """List audit log entries with filters (admin only)."""
    results = list(_audit_logs)

    if action:
        results = [e for e in results if e["action"] == action]
    if resource:
        results = [e for e in results if e["resource"] == resource]
    if user_email:
        results = [e for e in results if user_email.lower() in e["user_email"].lower()]
    if status_filter:
        results = [e for e in results if e["status"] == status_filter]

    # Sort by timestamp descending
    results.sort(key=lambda e: e["timestamp"], reverse=True)

    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size

    return {"logs": results[start:end], "total": total, "page": page, "page_size": page_size}


@router.get("/stats")
async def audit_stats(
    current_user: dict = Depends(require_role("ADMIN", "LEGAL_ADMIN")),
):
    """Get audit log statistics."""
    total = len(_audit_logs)

    # Actions breakdown
    action_counts: dict = {}
    resource_counts: dict = {}
    for entry in _audit_logs:
        action_counts[entry["action"]] = action_counts.get(entry["action"], 0) + 1
        resource_counts[entry["resource"]] = resource_counts.get(entry["resource"], 0) + 1

    # Sort by count
    top_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_resources = sorted(resource_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "total_entries": total,
        "actions": [{"action": a, "count": c} for a, c in top_actions],
        "resources": [{"resource": r, "count": c} for r, c in top_resources],
        "unique_users": len(set(e["user_email"] for e in _audit_logs)),
    }


@router.get("/actions")
async def list_action_types(
    current_user: dict = Depends(require_role("ADMIN", "LEGAL_ADMIN")),
):
    """List all unique action types."""
    actions = sorted(set(e["action"] for e in _audit_logs))
    return {"actions": actions}
