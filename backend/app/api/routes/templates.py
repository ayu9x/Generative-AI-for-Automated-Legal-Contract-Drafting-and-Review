"""Contract template browsing routes."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/templates", tags=["Templates"])


# ── In-Memory Template Store ────────────────────────────────────────

TEMPLATE_CATEGORIES = [
    {"id": "nda", "name": "Non-Disclosure Agreement", "icon": "🔒", "count": 8},
    {"id": "employment", "name": "Employment Contract", "icon": "👔", "count": 6},
    {"id": "service", "name": "Service Agreement", "icon": "🤝", "count": 7},
    {"id": "saas", "name": "SaaS / Software License", "icon": "💻", "count": 5},
    {"id": "consulting", "name": "Consulting Agreement", "icon": "📋", "count": 4},
    {"id": "partnership", "name": "Partnership Agreement", "icon": "🏢", "count": 3},
    {"id": "lease", "name": "Lease / Rental Agreement", "icon": "🏠", "count": 4},
    {"id": "ip", "name": "Intellectual Property", "icon": "💡", "count": 3},
    {"id": "vendor", "name": "Vendor / Supplier", "icon": "📦", "count": 3},
    {"id": "merger", "name": "M&A / Investment", "icon": "📈", "count": 3},
]

_templates = [
    # NDA Templates
    {"id": "nda-mutual", "name": "Mutual NDA", "category": "nda", "description": "Bilateral confidentiality agreement for two parties sharing sensitive information.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 4, "popularity": 95},
    {"id": "nda-unilateral", "name": "Unilateral NDA", "category": "nda", "description": "One-way confidentiality agreement protecting a single party's information.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 3, "popularity": 88},
    {"id": "nda-employee", "name": "Employee NDA", "category": "nda", "description": "Confidentiality agreement for employees handling proprietary information.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 3, "popularity": 82},
    {"id": "nda-multilateral", "name": "Multilateral NDA", "category": "nda", "description": "Confidentiality agreement involving three or more parties.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 6, "popularity": 45},
    {"id": "nda-gdpr", "name": "GDPR-Compliant NDA", "category": "nda", "description": "NDA with GDPR data processing provisions for EU operations.", "jurisdiction": "EU-GDPR", "risk_level": "medium", "estimated_pages": 7, "popularity": 72},
    {"id": "nda-tech-startup", "name": "Tech Startup NDA", "category": "nda", "description": "NDA tailored for technology startups sharing proprietary tech details.", "jurisdiction": "US-CA", "risk_level": "low", "estimated_pages": 4, "popularity": 78},
    {"id": "nda-healthcare", "name": "Healthcare NDA (HIPAA)", "category": "nda", "description": "NDA with HIPAA-compliant data handling provisions.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 6, "popularity": 65},
    {"id": "nda-financial", "name": "Financial Services NDA", "category": "nda", "description": "NDA designed for financial institutions and investment discussions.", "jurisdiction": "US-NY", "risk_level": "medium", "estimated_pages": 5, "popularity": 58},

    # Employment Templates
    {"id": "emp-fulltime", "name": "Full-Time Employment", "category": "employment", "description": "Standard employment contract for full-time positions with benefits.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 8, "popularity": 90},
    {"id": "emp-parttime", "name": "Part-Time Employment", "category": "employment", "description": "Employment contract for part-time positions with limited benefits.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 6, "popularity": 70},
    {"id": "emp-contractor", "name": "Independent Contractor", "category": "employment", "description": "Agreement for independent contractor engagements with scope of work.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 7, "popularity": 85},
    {"id": "emp-executive", "name": "Executive Employment", "category": "employment", "description": "Senior executive employment agreement with equity and bonus provisions.", "jurisdiction": "US-Federal", "risk_level": "high", "estimated_pages": 15, "popularity": 55},
    {"id": "emp-internship", "name": "Internship Agreement", "category": "employment", "description": "Agreement for internship positions with learning objectives.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 4, "popularity": 60},
    {"id": "emp-noncompete", "name": "Non-Compete Agreement", "category": "employment", "description": "Restrictive covenant preventing competition after employment ends.", "jurisdiction": "US-Federal", "risk_level": "high", "estimated_pages": 3, "popularity": 75},

    # Service Templates
    {"id": "svc-master", "name": "Master Service Agreement (MSA)", "category": "service", "description": "Comprehensive framework agreement governing ongoing service relationships.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 20, "popularity": 92},
    {"id": "svc-sow", "name": "Statement of Work (SOW)", "category": "service", "description": "Detailed scope document defining specific project deliverables.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 5, "popularity": 88},
    {"id": "svc-professional", "name": "Professional Services", "category": "service", "description": "Agreement for professional service engagements (legal, accounting, etc.).", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 10, "popularity": 76},
    {"id": "svc-managed", "name": "Managed Services Agreement", "category": "service", "description": "Agreement for ongoing managed IT or business services.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 12, "popularity": 62},
    {"id": "svc-maintenance", "name": "Maintenance & Support", "category": "service", "description": "Service-level agreement for ongoing maintenance and technical support.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 8, "popularity": 68},
    {"id": "svc-outsourcing", "name": "Outsourcing Agreement", "category": "service", "description": "Comprehensive outsourcing engagement agreement with KPIs.", "jurisdiction": "US-Federal", "risk_level": "high", "estimated_pages": 25, "popularity": 48},
    {"id": "svc-freelance", "name": "Freelance Services", "category": "service", "description": "Simple agreement for freelance and gig-based work engagements.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 4, "popularity": 82},

    # SaaS Templates
    {"id": "saas-standard", "name": "SaaS Subscription Agreement", "category": "saas", "description": "Standard software-as-a-service subscription with usage terms.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 12, "popularity": 86},
    {"id": "saas-enterprise", "name": "Enterprise Software License", "category": "saas", "description": "Enterprise-grade software licensing with SLA and support terms.", "jurisdiction": "US-Federal", "risk_level": "high", "estimated_pages": 18, "popularity": 72},
    {"id": "saas-api", "name": "API License Agreement", "category": "saas", "description": "Agreement governing API access, rate limits, and data usage.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 8, "popularity": 64},
    {"id": "saas-reseller", "name": "Software Reseller Agreement", "category": "saas", "description": "Agreement allowing resale of software products or services.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 10, "popularity": 42},
    {"id": "saas-dpa", "name": "Data Processing Agreement (DPA)", "category": "saas", "description": "GDPR/CCPA-compliant data processing agreement for SaaS vendors.", "jurisdiction": "EU-GDPR", "risk_level": "high", "estimated_pages": 10, "popularity": 78},

    # Consulting Templates
    {"id": "consulting-standard", "name": "Standard Consulting Agreement", "category": "consulting", "description": "General consulting services agreement with deliverables and milestones.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 8, "popularity": 80},
    {"id": "consulting-retainer", "name": "Retainer Agreement", "category": "consulting", "description": "Ongoing retainer-based consulting engagement agreement.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 6, "popularity": 65},
    {"id": "consulting-advisory", "name": "Advisory Board Agreement", "category": "consulting", "description": "Agreement for advisory board member roles and compensation.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 5, "popularity": 48},
    {"id": "consulting-management", "name": "Management Consulting MSA", "category": "consulting", "description": "Master agreement for management consulting engagements.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 14, "popularity": 55},

    # Partnership Templates
    {"id": "partner-general", "name": "General Partnership", "category": "partnership", "description": "Agreement forming a general partnership with shared responsibilities.", "jurisdiction": "US-Federal", "risk_level": "high", "estimated_pages": 15, "popularity": 52},
    {"id": "partner-limited", "name": "Limited Partnership", "category": "partnership", "description": "Limited partnership agreement with GP and LP roles defined.", "jurisdiction": "US-DE", "risk_level": "high", "estimated_pages": 20, "popularity": 45},
    {"id": "partner-joint-venture", "name": "Joint Venture Agreement", "category": "partnership", "description": "Agreement for a joint business venture between two or more parties.", "jurisdiction": "US-Federal", "risk_level": "high", "estimated_pages": 18, "popularity": 58},

    # Lease Templates
    {"id": "lease-commercial", "name": "Commercial Lease", "category": "lease", "description": "Commercial property lease agreement for office or retail space.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 15, "popularity": 74},
    {"id": "lease-residential", "name": "Residential Lease", "category": "lease", "description": "Standard residential rental agreement for apartment or house.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 8, "popularity": 85},
    {"id": "lease-equipment", "name": "Equipment Lease", "category": "lease", "description": "Agreement for leasing equipment, machinery, or vehicles.", "jurisdiction": "US-Federal", "risk_level": "low", "estimated_pages": 6, "popularity": 60},
    {"id": "lease-sublease", "name": "Sublease Agreement", "category": "lease", "description": "Agreement allowing a tenant to sublease property to a third party.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 5, "popularity": 45},

    # IP Templates
    {"id": "ip-assignment", "name": "IP Assignment Agreement", "category": "ip", "description": "Agreement transferring intellectual property rights between parties.", "jurisdiction": "US-Federal", "risk_level": "high", "estimated_pages": 6, "popularity": 68},
    {"id": "ip-licensing", "name": "IP Licensing Agreement", "category": "ip", "description": "Agreement licensing intellectual property for use by another party.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 10, "popularity": 72},
    {"id": "ip-trademark", "name": "Trademark License", "category": "ip", "description": "Agreement licensing trademark usage with quality control provisions.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 8, "popularity": 50},

    # Vendor Templates
    {"id": "vendor-supply", "name": "Supply Agreement", "category": "vendor", "description": "Agreement for ongoing supply of goods or materials.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 12, "popularity": 65},
    {"id": "vendor-distribution", "name": "Distribution Agreement", "category": "vendor", "description": "Agreement granting distribution rights for products in specific regions.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 14, "popularity": 52},
    {"id": "vendor-procurement", "name": "Procurement Agreement", "category": "vendor", "description": "Master procurement contract for bulk purchasing arrangements.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 10, "popularity": 48},

    # M&A / Investment Templates
    {"id": "ma-letter-of-intent", "name": "Letter of Intent (LOI)", "category": "merger", "description": "Non-binding letter expressing intent to acquire or invest.", "jurisdiction": "US-Federal", "risk_level": "medium", "estimated_pages": 5, "popularity": 70},
    {"id": "ma-share-purchase", "name": "Share Purchase Agreement", "category": "merger", "description": "Agreement for purchasing shares or equity in a company.", "jurisdiction": "US-DE", "risk_level": "high", "estimated_pages": 30, "popularity": 55},
    {"id": "ma-investment", "name": "Investment Agreement", "category": "merger", "description": "Agreement for venture capital or angel investment with terms.", "jurisdiction": "US-DE", "risk_level": "high", "estimated_pages": 20, "popularity": 62},
]

# Add created_at and version to all templates
for t in _templates:
    t["created_at"] = "2025-01-15T00:00:00Z"
    t["version"] = "1.0"
    t["tags"] = [t["category"], t["risk_level"], t["jurisdiction"].split("-")[0].lower()]


# ── Routes ───────────────────────────────────────────────────────────

@router.get("/categories")
async def list_categories(current_user: dict = Depends(get_current_user)):
    """List all template categories."""
    return {"categories": TEMPLATE_CATEGORIES, "total": len(TEMPLATE_CATEGORIES)}


@router.get("/")
async def list_templates(
    category: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query(default="popularity", regex="^(popularity|name|estimated_pages)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List templates with optional filters."""
    results = list(_templates)

    if category:
        results = [t for t in results if t["category"] == category]
    if jurisdiction:
        results = [t for t in results if t["jurisdiction"] == jurisdiction]
    if risk_level:
        results = [t for t in results if t["risk_level"] == risk_level]
    if search:
        search_lower = search.lower()
        results = [t for t in results if search_lower in t["name"].lower() or search_lower in t["description"].lower()]

    # Sort
    reverse = sort_by == "popularity"
    results.sort(key=lambda t: t.get(sort_by, ""), reverse=reverse)

    # Paginate
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = results[start:end]

    return {"templates": paginated, "total": total, "page": page, "page_size": page_size}


@router.get("/{template_id}")
async def get_template(template_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific template by ID."""
    template = next((t for t in _templates if t["id"] == template_id), None)
    if not template:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    # Add a preview section
    enriched = {**template, "preview": _get_template_preview(template)}
    return enriched


def _get_template_preview(template: dict) -> str:
    """Generate a brief preview of the template structure."""
    previews = {
        "nda": "1. Definition of Confidential Information\n2. Obligations of Receiving Party\n3. Exclusions from Confidentiality\n4. Term and Termination\n5. Return of Materials\n6. Remedies\n7. General Provisions",
        "employment": "1. Position and Duties\n2. Compensation and Benefits\n3. Work Schedule\n4. Confidentiality\n5. Intellectual Property\n6. Termination\n7. Non-Compete / Non-Solicitation\n8. General Provisions",
        "service": "1. Scope of Services\n2. Deliverables and Timeline\n3. Fees and Payment Terms\n4. Warranties and Representations\n5. Limitation of Liability\n6. Indemnification\n7. Termination\n8. Governing Law",
        "saas": "1. License Grant\n2. Usage Restrictions\n3. Subscription Terms\n4. Service Level Agreement\n5. Data Protection\n6. Intellectual Property\n7. Limitation of Liability\n8. Termination",
        "consulting": "1. Engagement Scope\n2. Deliverables\n3. Fees and Expenses\n4. Timeline and Milestones\n5. Confidentiality\n6. Intellectual Property\n7. Termination\n8. Indemnification",
        "partnership": "1. Partnership Formation\n2. Capital Contributions\n3. Profit/Loss Distribution\n4. Management and Voting\n5. Partner Responsibilities\n6. Dissolution\n7. Non-Compete\n8. Dispute Resolution",
        "lease": "1. Premises Description\n2. Term and Renewal\n3. Rent and Security Deposit\n4. Maintenance and Repairs\n5. Insurance\n6. Default and Remedies\n7. Termination\n8. Governing Law",
        "ip": "1. IP Description\n2. Grant of Rights\n3. Restrictions\n4. Compensation / Royalties\n5. Warranties\n6. Infringement\n7. Term and Termination\n8. Governing Law",
        "vendor": "1. Products / Services Description\n2. Pricing and Payment\n3. Delivery and Acceptance\n4. Warranties\n5. Liability\n6. Indemnification\n7. Termination\n8. Governing Law",
        "merger": "1. Transaction Structure\n2. Purchase Price\n3. Representations and Warranties\n4. Conditions to Closing\n5. Indemnification\n6. Non-Compete\n7. Confidentiality\n8. Governing Law",
    }
    return previews.get(template["category"], "Template structure not available.")
