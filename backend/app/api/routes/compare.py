"""
Contract Comparison API — Side-by-side diff engine.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import difflib
import uuid
from datetime import datetime

router = APIRouter(prefix="/compare", tags=["Compare"])


class CompareRequest(BaseModel):
    text_a: str
    text_b: str
    label_a: str = "Document A"
    label_b: str = "Document B"


class DiffLine(BaseModel):
    line_number: int
    type: str  # "added", "removed", "modified", "unchanged"
    content_a: Optional[str] = None
    content_b: Optional[str] = None


# ── In-memory store for comparison history ──────────────────────────

_comparison_history: list[dict] = []


@router.post("/")
async def compare_documents(req: CompareRequest):
    """Compare two contract texts and return diff results."""
    lines_a = req.text_a.splitlines()
    lines_b = req.text_b.splitlines()

    matcher = difflib.SequenceMatcher(None, lines_a, lines_b)
    diff_lines = []
    line_num = 0

    added_count = 0
    removed_count = 0
    modified_count = 0
    unchanged_count = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i in range(i1, i2):
                line_num += 1
                diff_lines.append({
                    "line_number": line_num,
                    "type": "unchanged",
                    "content_a": lines_a[i],
                    "content_b": lines_b[j1 + (i - i1)],
                })
                unchanged_count += 1
        elif tag == "replace":
            max_len = max(i2 - i1, j2 - j1)
            for k in range(max_len):
                line_num += 1
                diff_lines.append({
                    "line_number": line_num,
                    "type": "modified",
                    "content_a": lines_a[i1 + k] if (i1 + k) < i2 else None,
                    "content_b": lines_b[j1 + k] if (j1 + k) < j2 else None,
                })
                modified_count += 1
        elif tag == "delete":
            for i in range(i1, i2):
                line_num += 1
                diff_lines.append({
                    "line_number": line_num,
                    "type": "removed",
                    "content_a": lines_a[i],
                    "content_b": None,
                })
                removed_count += 1
        elif tag == "insert":
            for j in range(j1, j2):
                line_num += 1
                diff_lines.append({
                    "line_number": line_num,
                    "type": "added",
                    "content_a": None,
                    "content_b": lines_b[j],
                })
                added_count += 1

    similarity = round(matcher.ratio() * 100, 1)

    comparison_id = str(uuid.uuid4())[:8]
    result = {
        "comparison_id": comparison_id,
        "label_a": req.label_a,
        "label_b": req.label_b,
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_lines": line_num,
            "added": added_count,
            "removed": removed_count,
            "modified": modified_count,
            "unchanged": unchanged_count,
            "similarity_percent": similarity,
        },
        "diff_lines": diff_lines,
        "risk_impact": _assess_risk_impact(diff_lines),
    }

    _comparison_history.append({
        "id": comparison_id,
        "label_a": req.label_a,
        "label_b": req.label_b,
        "timestamp": result["timestamp"],
        "summary": result["summary"],
    })

    return result


@router.get("/summary")
async def get_comparison_summary():
    """Get summary of previous comparisons."""
    return {
        "total_comparisons": len(_comparison_history),
        "recent": _comparison_history[-10:][::-1],
    }


def _assess_risk_impact(diff_lines: list[dict]) -> dict:
    """Analyze changes for risk-relevant keywords."""
    risk_keywords = {
        "high": ["indemnification", "liability", "termination", "penalty", "breach", "damages", "warrant"],
        "medium": ["confidential", "obligation", "compliance", "restriction", "exclusion", "limitation"],
        "low": ["notice", "amendment", "assignment", "governing law", "dispute", "arbitration"],
    }

    flagged = []
    for line in diff_lines:
        if line["type"] in ("added", "modified", "removed"):
            text = (line.get("content_a") or "") + " " + (line.get("content_b") or "")
            text_lower = text.lower()
            for level, words in risk_keywords.items():
                for word in words:
                    if word in text_lower:
                        flagged.append({
                            "line": line["line_number"],
                            "risk_level": level,
                            "keyword": word,
                            "change_type": line["type"],
                        })
                        break

    high_count = sum(1 for f in flagged if f["risk_level"] == "high")
    medium_count = sum(1 for f in flagged if f["risk_level"] == "medium")

    overall = "low"
    if high_count >= 2:
        overall = "high"
    elif high_count >= 1 or medium_count >= 3:
        overall = "medium"

    return {
        "overall_risk": overall,
        "flagged_changes": flagged[:20],
        "high_risk_changes": high_count,
        "medium_risk_changes": medium_count,
    }
