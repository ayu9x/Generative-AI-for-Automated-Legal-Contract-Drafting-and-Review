"""
Notifications API — User notification management.
"""

from fastapi import APIRouter, Depends
from typing import Optional
from datetime import datetime, timedelta
import uuid
import random

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ── In-memory notification store ────────────────────────────────────

def _seed_notifications() -> list[dict]:
    """Generate realistic demo notifications."""
    now = datetime.utcnow()
    templates = [
        {"type": "contract_created", "title": "Contract Generated", "message": "NDA Agreement — Mutual has been successfully generated.", "icon": "file-plus", "color": "green"},
        {"type": "review_complete", "title": "Review Complete", "message": "Risk analysis for Employment Contract is ready. High risk score detected.", "icon": "alert-triangle", "color": "red"},
        {"type": "compliance_pass", "title": "Compliance Check Passed", "message": "SaaS Agreement passed GDPR compliance verification.", "icon": "shield-check", "color": "green"},
        {"type": "deadline_approaching", "title": "Deadline Approaching", "message": "Service Agreement renewal due in 7 days.", "icon": "clock", "color": "yellow"},
        {"type": "contract_approved", "title": "Contract Approved", "message": "Master Service Agreement v2.1 has been approved by Legal.", "icon": "check-circle", "color": "green"},
        {"type": "version_created", "title": "New Version Created", "message": "NDA v1.3 created with updated arbitration clause.", "icon": "git-branch", "color": "blue"},
        {"type": "compliance_fail", "title": "Compliance Issue Found", "message": "Vendor Agreement has HIPAA compliance issues that need attention.", "icon": "alert-circle", "color": "red"},
        {"type": "comment_added", "title": "New Comment", "message": "Jane Smith commented on Licensing Agreement: 'Please review Section 4.2'", "icon": "message-circle", "color": "blue"},
        {"type": "deadline_overdue", "title": "Deadline Overdue", "message": "IP Assignment Agreement review was due 3 days ago.", "icon": "alert-triangle", "color": "red"},
        {"type": "template_update", "title": "Template Updated", "message": "Employment Agreement template updated to reflect new labor laws.", "icon": "refresh-cw", "color": "purple"},
        {"type": "contract_created", "title": "Contract Generated", "message": "Consulting Agreement — Fixed Fee has been generated.", "icon": "file-plus", "color": "green"},
        {"type": "review_complete", "title": "Review Complete", "message": "Risk analysis for Supply Agreement is ready. Medium risk.", "icon": "alert-triangle", "color": "yellow"},
        {"type": "deadline_approaching", "title": "Deadline Approaching", "message": "Non-Compete Agreement expires in 14 days.", "icon": "clock", "color": "yellow"},
        {"type": "contract_approved", "title": "Contract Approved", "message": "Data Processing Agreement has been approved.", "icon": "check-circle", "color": "green"},
        {"type": "compliance_pass", "title": "Compliance Check Passed", "message": "Joint Venture Agreement passed SOX compliance check.", "icon": "shield-check", "color": "green"},
    ]

    notifications = []
    for i, tmpl in enumerate(templates):
        notifications.append({
            "id": str(uuid.uuid4())[:8],
            "type": tmpl["type"],
            "title": tmpl["title"],
            "message": tmpl["message"],
            "icon": tmpl["icon"],
            "color": tmpl["color"],
            "is_read": i >= 5,  # First 5 are unread
            "created_at": (now - timedelta(minutes=random.randint(5, 2880) * (i + 1))).isoformat(),
            "link": f"/contracts/contract-{i + 1:03d}",
        })

    # Sort by created_at descending
    notifications.sort(key=lambda n: n["created_at"], reverse=True)
    return notifications


_notifications = _seed_notifications()


@router.get("/")
async def list_notifications(
    unread_only: bool = False,
    page: int = 1,
    page_size: int = 20,
):
    """List notifications for the logged-in user."""
    filtered = _notifications
    if unread_only:
        filtered = [n for n in filtered if not n["is_read"]]

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    items = filtered[start:end]

    unread_count = sum(1 for n in _notifications if not n["is_read"])

    return {
        "notifications": items,
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "page_size": page_size,
    }


@router.put("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """Mark a single notification as read."""
    for notif in _notifications:
        if notif["id"] == notification_id:
            notif["is_read"] = True
            return {"status": "ok", "id": notification_id}
    return {"status": "not_found"}


@router.put("/read-all")
async def mark_all_read():
    """Mark all notifications as read."""
    for notif in _notifications:
        notif["is_read"] = True
    return {"status": "ok", "count": len(_notifications)}


@router.get("/unread-count")
async def get_unread_count():
    """Get the count of unread notifications."""
    count = sum(1 for n in _notifications if not n["is_read"])
    return {"unread_count": count}
