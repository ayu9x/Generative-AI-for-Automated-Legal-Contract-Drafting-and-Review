"""Clause library routes — browsable library of reusable legal clauses."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/clauses", tags=["Clause Library"])


# ── In-Memory Clause Store ──────────────────────────────────────────

CLAUSE_CATEGORIES = [
    "Confidentiality",
    "Indemnification",
    "Limitation of Liability",
    "Termination",
    "Force Majeure",
    "Intellectual Property",
    "Dispute Resolution",
    "Non-Compete",
    "Data Protection",
    "Payment Terms",
    "Warranties",
    "Governing Law",
]

_clauses = [
    # Confidentiality
    {
        "id": "cl-conf-standard",
        "title": "Standard Confidentiality Clause",
        "category": "Confidentiality",
        "jurisdiction": "US-Federal",
        "risk_level": "low",
        "description": "Standard provision requiring parties to keep shared information confidential.",
        "text": '''Each party agrees to maintain in strict confidence all Confidential Information received from the other party. "Confidential Information" means any non-public information disclosed by either party to the other, whether orally, in writing, or by inspection, that is designated as confidential or that reasonably should be understood to be confidential given the nature of the information and circumstances of disclosure. The receiving party shall not disclose Confidential Information to any third party without prior written consent and shall use it solely for the purposes contemplated by this Agreement.''',
        "usage_count": 1245,
    },
    {
        "id": "cl-conf-mutual",
        "title": "Mutual Confidentiality Obligation",
        "category": "Confidentiality",
        "jurisdiction": "US-Federal",
        "risk_level": "low",
        "description": "Bilateral confidentiality obligation covering both parties equally.",
        "text": '''Both parties acknowledge that in the course of performing their obligations under this Agreement, each may have access to Confidential Information of the other. Each party agrees: (a) to hold the other's Confidential Information in strict confidence; (b) not to disclose such information to third parties without prior written consent; (c) to use such information solely for the purposes of this Agreement; and (d) to protect such information using the same degree of care it uses to protect its own confidential information, but in no event less than reasonable care.''',
        "usage_count": 980,
    },
    {
        "id": "cl-conf-exclusions",
        "title": "Confidentiality Exclusions",
        "category": "Confidentiality",
        "jurisdiction": "US-Federal",
        "risk_level": "low",
        "description": "Standard carve-outs from confidentiality obligations.",
        "text": '''The obligations of confidentiality shall not apply to information that: (a) is or becomes publicly available through no fault of the receiving party; (b) was rightfully in the receiving party's possession prior to disclosure; (c) is independently developed by the receiving party without use of or reference to the disclosing party's Confidential Information; (d) is rightfully received from a third party without restriction on disclosure; or (e) is required to be disclosed by law, regulation, or court order, provided that the receiving party gives prompt notice to the disclosing party.''',
        "usage_count": 875,
    },

    # Indemnification
    {
        "id": "cl-indem-mutual",
        "title": "Mutual Indemnification",
        "category": "Indemnification",
        "jurisdiction": "US-Federal",
        "risk_level": "medium",
        "description": "Both parties indemnify each other against third-party claims.",
        "text": '''Each party (the "Indemnifying Party") shall indemnify, defend, and hold harmless the other party and its officers, directors, employees, agents, and successors (the "Indemnified Parties") from and against any and all losses, damages, liabilities, costs, and expenses (including reasonable attorneys' fees) arising out of or relating to: (a) any breach of this Agreement by the Indemnifying Party; (b) any negligent or wrongful act or omission of the Indemnifying Party; or (c) any third-party claim arising from the Indemnifying Party's performance under this Agreement.''',
        "usage_count": 920,
    },
    {
        "id": "cl-indem-ip",
        "title": "IP Indemnification",
        "category": "Indemnification",
        "jurisdiction": "US-Federal",
        "risk_level": "high",
        "description": "Indemnification specifically for intellectual property infringement claims.",
        "text": '''Provider shall indemnify, defend, and hold harmless Client from and against any third-party claim that the Services or Deliverables infringe any patent, copyright, trademark, or trade secret of such third party. Provider shall pay all costs, damages, and attorneys' fees finally awarded against Client. Client shall: (a) promptly notify Provider of the claim; (b) grant Provider sole control of the defense and settlement; and (c) provide reasonable assistance at Provider's expense. If an injunction is obtained, Provider shall, at its option: (i) procure the right to continue use; (ii) modify the infringing item; or (iii) replace the infringing item with a non-infringing equivalent.''',
        "usage_count": 710,
    },

    # Limitation of Liability
    {
        "id": "cl-lol-standard",
        "title": "Limitation of Liability",
        "category": "Limitation of Liability",
        "jurisdiction": "US-Federal",
        "risk_level": "high",
        "description": "Standard cap on liability and exclusion of consequential damages.",
        "text": '''IN NO EVENT SHALL EITHER PARTY BE LIABLE TO THE OTHER FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, REGARDLESS OF THE CAUSE OF ACTION OR THE THEORY OF LIABILITY, EVEN IF SUCH PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. EACH PARTY'S TOTAL AGGREGATE LIABILITY ARISING OUT OF OR RELATED TO THIS AGREEMENT SHALL NOT EXCEED THE AMOUNTS PAID OR PAYABLE BY CLIENT TO PROVIDER UNDER THIS AGREEMENT DURING THE TWELVE (12) MONTHS PRECEDING THE EVENT GIVING RISE TO THE CLAIM.''',
        "usage_count": 1100,
    },
    {
        "id": "cl-lol-carveouts",
        "title": "Liability Carve-Outs",
        "category": "Limitation of Liability",
        "jurisdiction": "US-Federal",
        "risk_level": "high",
        "description": "Exceptions to liability limitations for willful misconduct, IP infringement, etc.",
        "text": '''The limitations of liability set forth above shall not apply to: (a) either party's indemnification obligations; (b) either party's breach of confidentiality obligations; (c) willful misconduct or gross negligence by either party; (d) Provider's infringement of Client's intellectual property rights; or (e) either party's breach of applicable data protection laws.''',
        "usage_count": 650,
    },

    # Termination
    {
        "id": "cl-term-convenience",
        "title": "Termination for Convenience",
        "category": "Termination",
        "jurisdiction": "US-Federal",
        "risk_level": "low",
        "description": "Allows either party to terminate with written notice.",
        "text": '''Either party may terminate this Agreement at any time, for any reason or no reason, upon thirty (30) days' prior written notice to the other party. Upon such termination: (a) all rights and licenses granted herein shall immediately terminate; (b) each party shall return or destroy all Confidential Information of the other; and (c) Client shall pay Provider for all Services performed and expenses incurred through the effective date of termination.''',
        "usage_count": 890,
    },
    {
        "id": "cl-term-cause",
        "title": "Termination for Cause",
        "category": "Termination",
        "jurisdiction": "US-Federal",
        "risk_level": "medium",
        "description": "Termination right triggered by material breach with cure period.",
        "text": '''Either party may terminate this Agreement upon written notice if the other party: (a) materially breaches this Agreement and fails to cure such breach within thirty (30) days after receiving written notice; (b) becomes insolvent, files for or has filed against it a petition in bankruptcy, makes an assignment for the benefit of creditors, or has a receiver appointed for a substantial part of its assets; or (c) ceases to conduct business in the normal course.''',
        "usage_count": 1050,
    },

    # Force Majeure
    {
        "id": "cl-fm-standard",
        "title": "Force Majeure",
        "category": "Force Majeure",
        "jurisdiction": "US-Federal",
        "risk_level": "low",
        "description": "Excuses performance delays caused by events beyond reasonable control.",
        "text": '''Neither party shall be liable for any delay or failure to perform its obligations under this Agreement due to causes beyond its reasonable control, including but not limited to: acts of God, natural disasters, war, terrorism, riots, embargoes, acts of civil or military authorities, fire, floods, epidemics or pandemics, strikes, shortages of transportation, facilities, fuel, energy, labor, or materials, or failures of telecommunications or power supply ("Force Majeure Event"). The affected party shall promptly notify the other party and use commercially reasonable efforts to mitigate the impact. If a Force Majeure Event continues for more than ninety (90) days, either party may terminate this Agreement upon written notice.''',
        "usage_count": 780,
    },

    # Intellectual Property
    {
        "id": "cl-ip-ownership",
        "title": "IP Ownership — Work for Hire",
        "category": "Intellectual Property",
        "jurisdiction": "US-Federal",
        "risk_level": "high",
        "description": "All work product created under the agreement belongs to the client.",
        "text": '''All Deliverables and work product created by Provider under this Agreement shall be considered "work made for hire" as defined by the U.S. Copyright Act. To the extent any Deliverable does not qualify as a work made for hire, Provider hereby irrevocably assigns to Client all right, title, and interest in and to such Deliverable, including all intellectual property rights therein. Provider shall execute all documents and take all actions reasonably requested by Client to evidence, perfect, or record such assignment.''',
        "usage_count": 830,
    },
    {
        "id": "cl-ip-license-back",
        "title": "License-Back to Provider",
        "category": "Intellectual Property",
        "jurisdiction": "US-Federal",
        "risk_level": "medium",
        "description": "Grants provider a license to use pre-existing IP incorporated in deliverables.",
        "text": '''Client hereby grants to Provider a non-exclusive, royalty-free, worldwide license to use, reproduce, and modify any Client Materials solely for the purpose of performing the Services. Provider retains all rights in its Pre-Existing IP and grants to Client a non-exclusive, perpetual, royalty-free license to use any Pre-Existing IP incorporated into the Deliverables, solely in connection with Client's use of the Deliverables.''',
        "usage_count": 520,
    },

    # Dispute Resolution
    {
        "id": "cl-disp-arbitration",
        "title": "Binding Arbitration",
        "category": "Dispute Resolution",
        "jurisdiction": "US-Federal",
        "risk_level": "medium",
        "description": "Requires disputes to be resolved through binding arbitration.",
        "text": '''Any dispute, controversy, or claim arising out of or relating to this Agreement shall be settled by binding arbitration administered by the American Arbitration Association ("AAA") under its Commercial Arbitration Rules. The arbitration shall be conducted by a single arbitrator in [City, State]. The arbitrator's decision shall be final and binding and may be entered as a judgment in any court of competent jurisdiction. Each party shall bear its own costs, and the parties shall share equally the fees and expenses of the arbitrator and the AAA.''',
        "usage_count": 680,
    },
    {
        "id": "cl-disp-mediation",
        "title": "Mediation Then Arbitration",
        "category": "Dispute Resolution",
        "jurisdiction": "US-Federal",
        "risk_level": "low",
        "description": "Requires mediation before escalating to arbitration.",
        "text": '''The parties agree to first attempt to resolve any dispute through good-faith negotiation for a period of thirty (30) days. If the dispute remains unresolved, the parties shall submit the dispute to non-binding mediation. If mediation does not resolve the dispute within sixty (60) days, either party may submit the dispute to binding arbitration in accordance with the rules of the American Arbitration Association.''',
        "usage_count": 450,
    },

    # Non-Compete
    {
        "id": "cl-nc-employee",
        "title": "Employee Non-Compete",
        "category": "Non-Compete",
        "jurisdiction": "US-Federal",
        "risk_level": "high",
        "description": "Restricts employee from competing during and after employment.",
        "text": '''During the term of employment and for a period of twelve (12) months following termination for any reason, Employee shall not, directly or indirectly: (a) engage in any business that competes with the Company's business within a 50-mile radius of the Company's principal place of business; (b) solicit any customer, client, or business partner of the Company; or (c) induce any employee, contractor, or consultant of the Company to terminate their engagement. Employee acknowledges that these restrictions are reasonable and necessary to protect the Company's legitimate business interests.''',
        "usage_count": 590,
    },

    # Data Protection
    {
        "id": "cl-dp-gdpr",
        "title": "GDPR Data Processing Clause",
        "category": "Data Protection",
        "jurisdiction": "EU-GDPR",
        "risk_level": "high",
        "description": "GDPR-compliant data processing provisions.",
        "text": '''The Data Processor shall: (a) process Personal Data only on documented instructions from the Data Controller; (b) ensure that persons authorized to process Personal Data have committed to confidentiality; (c) implement appropriate technical and organizational measures to ensure a level of security appropriate to the risk; (d) not engage another processor without prior specific or general written authorization; (e) assist the Controller in responding to data subject rights requests; (f) delete or return all Personal Data upon termination; and (g) make available all information necessary to demonstrate compliance with GDPR obligations.''',
        "usage_count": 720,
    },
    {
        "id": "cl-dp-ccpa",
        "title": "CCPA Data Privacy Clause",
        "category": "Data Protection",
        "jurisdiction": "US-CA",
        "risk_level": "high",
        "description": "California Consumer Privacy Act (CCPA) compliance provisions.",
        "text": '''Service Provider certifies that it understands the restrictions of the California Consumer Privacy Act (CCPA) and will comply with them. Service Provider shall: (a) not sell Personal Information; (b) not retain, use, or disclose Personal Information for any purpose other than performing Services; (c) not retain, use, or disclose Personal Information outside of the direct business relationship; and (d) grant Consumer the right to opt-out of the sale of their Personal Information.''',
        "usage_count": 580,
    },

    # Payment Terms
    {
        "id": "cl-pay-net30",
        "title": "Net 30 Payment Terms",
        "category": "Payment Terms",
        "jurisdiction": "US-Federal",
        "risk_level": "low",
        "description": "Standard payment terms with 30-day invoice cycle.",
        "text": '''Client shall pay all undisputed invoices within thirty (30) days of receipt. Invoices shall be itemized and include a description of the Services performed. Late payments shall accrue interest at the lesser of 1.5% per month or the maximum rate permitted by applicable law. If any amount is more than sixty (60) days overdue, Provider may suspend performance until all overdue amounts are paid in full.''',
        "usage_count": 940,
    },
    {
        "id": "cl-pay-milestone",
        "title": "Milestone-Based Payments",
        "category": "Payment Terms",
        "jurisdiction": "US-Federal",
        "risk_level": "low",
        "description": "Payment tied to project milestones and deliverable acceptance.",
        "text": '''Fees shall be paid upon completion and acceptance of each milestone as defined in the Statement of Work. Client shall review and accept or reject each Deliverable within ten (10) business days of delivery. If Client does not respond within ten (10) business days, the Deliverable shall be deemed accepted. Upon acceptance, Client shall pay the associated milestone payment within fifteen (15) days.''',
        "usage_count": 670,
    },

    # Warranties
    {
        "id": "cl-warr-services",
        "title": "Services Warranty",
        "category": "Warranties",
        "jurisdiction": "US-Federal",
        "risk_level": "medium",
        "description": "Warranty that services will be performed in a professional manner.",
        "text": '''Provider warrants that the Services shall be performed in a professional and workmanlike manner consistent with generally accepted industry standards. If the Services fail to conform to this warranty, Client must notify Provider within thirty (30) days, and Provider shall re-perform the non-conforming Services at no additional cost. THIS WARRANTY IS THE SOLE AND EXCLUSIVE WARRANTY WITH RESPECT TO THE SERVICES, AND PROVIDER DISCLAIMS ALL OTHER WARRANTIES, EXPRESS OR IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.''',
        "usage_count": 810,
    },

    # Governing Law
    {
        "id": "cl-gov-delaware",
        "title": "Delaware Governing Law",
        "category": "Governing Law",
        "jurisdiction": "US-DE",
        "risk_level": "low",
        "description": "Specifies Delaware as the governing law jurisdiction.",
        "text": '''This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, without regard to its conflict of law principles. Any legal action or proceeding arising under this Agreement shall be brought exclusively in the federal or state courts located in Wilmington, Delaware, and the parties hereby consent to personal jurisdiction and venue therein.''',
        "usage_count": 760,
    },
    {
        "id": "cl-gov-ny",
        "title": "New York Governing Law",
        "category": "Governing Law",
        "jurisdiction": "US-NY",
        "risk_level": "low",
        "description": "Specifies New York as the governing law jurisdiction.",
        "text": '''This Agreement shall be governed by and construed in accordance with the laws of the State of New York, without regard to its conflict of law provisions. The parties agree to submit to the exclusive jurisdiction of the courts of the State of New York sitting in the Borough of Manhattan, City of New York, and the United States District Court for the Southern District of New York, for the resolution of any disputes arising under this Agreement.''',
        "usage_count": 820,
    },
    {
        "id": "cl-gov-california",
        "title": "California Governing Law",
        "category": "Governing Law",
        "jurisdiction": "US-CA",
        "risk_level": "low",
        "description": "Specifies California as the governing law jurisdiction.",
        "text": '''This Agreement shall be governed by the laws of the State of California without regard to its conflict of law provisions. Any disputes arising from this Agreement shall be resolved in the state or federal courts located in San Francisco County, California. Both parties consent to the exclusive jurisdiction and venue of such courts.''',
        "usage_count": 690,
    },
]


# ── Routes ───────────────────────────────────────────────────────────

@router.get("/categories")
async def list_clause_categories(current_user: dict = Depends(get_current_user)):
    """List all clause categories."""
    return {"categories": CLAUSE_CATEGORIES}


@router.get("/")
async def list_clauses(
    category: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List clauses with optional filters."""
    results = list(_clauses)

    if category:
        results = [c for c in results if c["category"] == category]
    if jurisdiction:
        results = [c for c in results if c["jurisdiction"] == jurisdiction]
    if risk_level:
        results = [c for c in results if c["risk_level"] == risk_level]
    if search:
        s = search.lower()
        results = [c for c in results if s in c["title"].lower() or s in c["description"].lower() or s in c["text"].lower()]

    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size

    # Return without full text in listing (preview only)
    listing = []
    for c in results[start:end]:
        listing.append({**c, "text": c["text"][:200] + "..." if len(c["text"]) > 200 else c["text"]})

    return {"clauses": listing, "total": total, "page": page, "page_size": page_size}


@router.get("/{clause_id}")
async def get_clause(clause_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific clause by ID with full text."""
    clause = next((c for c in _clauses if c["id"] == clause_id), None)
    if not clause:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clause not found")
    return clause


@router.post("/explain")
async def explain_clause(
    data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Get an AI explanation of a clause in plain English."""
    clause_text = data.get("clause_text", "")
    audience = data.get("audience", "non-lawyer")

    if not clause_text:
        raise HTTPException(status_code=400, detail="clause_text is required")

    # Generate explanation (mock — in production this would call the LLM)
    explanation = _generate_explanation(clause_text, audience)

    return {
        "original_text": clause_text[:500],
        "explanation": explanation,
        "audience": audience,
        "key_points": _extract_key_points(clause_text),
    }


def _generate_explanation(clause_text: str, audience: str) -> str:
    """Generate a plain-English explanation of the clause."""
    text_lower = clause_text.lower()

    if "confidential" in text_lower:
        return "This clause requires the parties to keep sensitive information private. If someone shares confidential business details with you, you cannot share them with others or use them for your own benefit. There are usually exceptions for information that becomes public knowledge or that you already knew."
    elif "indemnif" in text_lower:
        return "This is a protection clause. If one party's actions cause the other party to be sued or incur losses, the responsible party must cover those costs — including legal fees and damages. Think of it as a promise to 'make the other party whole' if something goes wrong."
    elif "limitation of liability" in text_lower or "shall not exceed" in text_lower:
        return "This clause puts a ceiling on how much money one party can owe the other if things go wrong. It typically excludes indirect damages (like lost profits) and caps the total liability to a specific amount, often tied to what was paid under the contract."
    elif "terminat" in text_lower:
        return "This clause explains how and when the agreement can be ended. It usually covers both voluntary termination (either party wants out) and termination for cause (one party broke the rules). It also describes what happens after the contract ends — like returning materials and paying for work completed."
    elif "force majeure" in text_lower:
        return "This is the 'acts of God' clause. It says that if something completely outside either party's control happens — like a natural disaster, pandemic, or war — neither party is held responsible for delays or failures to perform their obligations."
    elif "intellectual property" in text_lower or "work made for hire" in text_lower:
        return "This clause determines who owns the creative work, inventions, or content produced during the project. In a 'work for hire' arrangement, the client owns everything the service provider creates. The provider gives up all ownership rights."
    elif "arbitration" in text_lower:
        return "Instead of going to court, this clause requires disputes to be resolved through arbitration — a private process where a neutral third party (the arbitrator) makes a binding decision. It's generally faster and less expensive than litigation."
    elif "non-compete" in text_lower or "shall not.*compete" in text_lower:
        return "This clause prevents someone from working for a competitor or starting a competing business for a specified period after leaving. It's designed to protect business secrets and client relationships."
    elif "gdpr" in text_lower or "personal data" in text_lower:
        return "This clause ensures compliance with data privacy regulations (like GDPR). It specifies how personal data must be handled, stored, and protected. The data processor must follow strict rules about what they can do with the data and must delete it when the contract ends."
    elif "payment" in text_lower or "invoice" in text_lower:
        return "This clause sets the rules for when and how payments must be made. It typically includes the payment deadline, late payment penalties, and what happens if a payment is disputed or overdue."
    elif "warrant" in text_lower:
        return "This is a guarantee clause. The service provider promises that the work will meet professional standards. If it doesn't, the provider must fix it at no extra cost. However, it usually disclaims other guarantees beyond this basic promise."
    elif "governing law" in text_lower or "governed by" in text_lower:
        return "This clause determines which state or country's laws will be used to interpret the contract and where any lawsuits must be filed. This is important because legal rules differ between jurisdictions and can significantly affect the outcome of disputes."
    else:
        return "This is a standard legal provision that establishes specific rights and obligations between the parties. It defines the scope of each party's responsibilities and the consequences for non-compliance. For a detailed analysis, consider consulting with a licensed attorney."


def _extract_key_points(clause_text: str) -> list:
    """Extract key points from a clause."""
    text_lower = clause_text.lower()
    points = []

    if "shall" in text_lower or "must" in text_lower:
        points.append("Contains mandatory obligations")
    if "not" in text_lower or "shall not" in text_lower:
        points.append("Contains prohibitions or restrictions")
    if "thirty (30) days" in text_lower or "30 days" in text_lower:
        points.append("Includes a 30-day notice or cure period")
    if "twelve (12) months" in text_lower or "12 months" in text_lower:
        points.append("Has a 12-month duration component")
    if "reasonable" in text_lower:
        points.append("Uses 'reasonableness' standard (subjective)")
    if "indemnif" in text_lower:
        points.append("Involves indemnification obligations")
    if "damages" in text_lower:
        points.append("Addresses damages and liability")
    if "confidential" in text_lower:
        points.append("Imposes confidentiality requirements")
    if "terminate" in text_lower or "termination" in text_lower:
        points.append("Addresses termination conditions")
    if "governing law" in text_lower or "governed by" in text_lower:
        points.append("Specifies governing jurisdiction")

    if not points:
        points.append("Standard contractual provision")

    return points[:5]
