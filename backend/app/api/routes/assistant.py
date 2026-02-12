"""
AI Legal Chat Assistant API — Interactive legal Q&A.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import uuid
import random
from datetime import datetime

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None


# ── Pre-built legal responses for demo mode ─────────────────────────

_legal_responses = {
    "force majeure": {
        "response": """**Force Majeure** is a contract provision that frees both parties from obligation when an extraordinary event directly prevents one or both parties from performing.

**Key Elements:**
• Events beyond reasonable control (natural disasters, war, pandemics, government actions)
• The event must make performance impossible, not merely difficult or expensive
• The affected party must provide timely notice
• Duty to mitigate damages remains

**Common Pitfalls:**
1. Overly broad definitions that could be abused
2. Failure to specify notice requirements
3. Not addressing partial performance scenarios
4. Missing termination rights after extended force majeure periods

**Recommendation:** Always define specific triggering events rather than using vague language. Include a notice period (typically 30 days) and a termination right if the force majeure event continues beyond 90-180 days.""",
        "category": "Contract Clauses",
    },
    "nda": {
        "response": """**Non-Disclosure Agreement (NDA)** is a legally binding contract that establishes a confidential relationship between parties.

**Types of NDAs:**
1. **Unilateral NDA** — One party discloses, the other protects
2. **Mutual NDA** — Both parties share and protect information
3. **Multilateral NDA** — Three or more parties involved

**Essential Elements:**
• Clear definition of "Confidential Information"
• Obligations of the receiving party
• Exclusions from confidentiality (publicly known, independently developed)
• Term and termination provisions
• Remedies for breach (injunctive relief, damages)

**Risk Considerations:**
- Duration: 2-5 years is standard; perpetual NDAs face enforceability challenges
- Scope: Too broad = unenforceable; too narrow = inadequate protection
- Carve-outs: Always include standard exclusions

**Best Practice:** Use a mutual NDA when both parties will share sensitive information. Include specific examples of what constitutes confidential information.""",
        "category": "Agreement Types",
    },
    "gdpr": {
        "response": """**GDPR (General Data Protection Regulation)** requirements for contracts:

**Key Contract Requirements:**
1. **Data Processing Agreement (DPA)** — Required when sharing personal data with processors
2. **Privacy Notice** — Must inform data subjects about processing
3. **Lawful Basis** — Contract must specify legal basis for processing
4. **Data Subject Rights** — Must address access, rectification, erasure, portability

**Contract Clauses to Include:**
• Purpose limitation clause
• Data minimization obligations
• Security measures specification
• Sub-processor approval mechanism
• Data breach notification (72-hour requirement)
• Cross-border transfer safeguards (SCCs or adequacy decisions)
• Data retention and deletion schedules

**Penalties for Non-Compliance:**
- Up to €20 million or 4% of global annual revenue (whichever is higher)
- Reputational damage and loss of customer trust

**Recommendation:** Include a comprehensive DPA as an appendix to any contract involving EU personal data. Use the EU Standard Contractual Clauses for international transfers.""",
        "category": "Compliance",
    },
    "indemnification": {
        "response": """**Indemnification Clauses** allocate risk between contracting parties by requiring one party to compensate the other for certain losses.

**Types:**
1. **Broad Form** — Indemnitor covers all losses, even if partially caused by indemnitee
2. **Intermediate Form** — Indemnitor covers losses except those caused solely by indemnitee
3. **Limited Form** — Indemnitor only covers losses caused by their own negligence

**Key Drafting Considerations:**
• **Scope:** Define what triggers indemnification (IP infringement, data breach, third-party claims)
• **Cap:** Set a maximum liability amount (common: 1-2x contract value)
• **Exclusions:** Carve out consequential, punitive, and indirect damages
• **Process:** Require prompt notice of claims and cooperation in defense
• **Insurance:** Require appropriate insurance coverage

**Common Mistakes:**
- Unlimited indemnification obligations
- Missing notice requirements
- No cap on liability
- Failing to address defense control

**Recommendation:** Always negotiate mutual indemnification with reasonable caps. Ensure the indemnifying party has the right to control the defense of third-party claims.""",
        "category": "Contract Clauses",
    },
    "termination": {
        "response": """**Termination Clauses** define how and when a contract can be ended.

**Types of Termination:**
1. **For Cause** — Material breach, insolvency, change of control
2. **For Convenience** — Either party can terminate with notice (30-90 days typical)
3. **Automatic** — Contract expires at end of term
4. **Mutual Agreement** — Both parties agree to terminate

**Essential Elements:**
• Notice period requirements (typically 30-90 days written notice)
• Cure period for breaches (15-30 days to remedy)
• Post-termination obligations (return of materials, surviving provisions)
• Transition assistance provisions
• Payment of outstanding obligations

**Surviving Provisions (typically):**
- Confidentiality obligations
- Indemnification commitments
- Limitation of liability
- Dispute resolution
- Intellectual property rights

**Recommendation:** Include both for-cause and for-convenience termination rights. Specify which provisions survive termination and for how long.""",
        "category": "Contract Clauses",
    },
}

_default_response = {
    "response": """Thank you for your question. Here's a general legal perspective:

**Key Considerations:**
1. **Context Matters** — Legal provisions should always be evaluated in the specific context of the agreement and jurisdiction
2. **Risk Assessment** — Consider the potential exposure and likelihood of disputes
3. **Industry Standards** — Review what's customary in your industry
4. **Regulatory Compliance** — Ensure clauses comply with applicable laws and regulations

**Recommended Actions:**
• Review the specific contract language carefully
• Consider consulting with a legal professional for complex matters
• Document all negotiations and agreed-upon changes
• Ensure all parties have a clear understanding of their obligations

**Useful Resources:**
- Use the **Clause Library** for pre-approved clause language
- Run a **Risk Analysis** to identify potential issues
- Check **Compliance Center** for regulatory requirements

*Note: This AI assistant provides general legal information for educational purposes. Always consult with a qualified attorney for specific legal advice.*""",
    "category": "General",
}


@router.post("/chat")
async def chat(msg: ChatMessage):
    """Send a message to the AI legal assistant."""
    message_lower = msg.message.lower()

    # Match against known topics
    matched_response = None
    matched_topic = None
    for keyword, resp in _legal_responses.items():
        if keyword in message_lower:
            matched_response = resp
            matched_topic = keyword
            break

    if not matched_response:
        matched_response = _default_response
        matched_topic = "general"

    return {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.utcnow().isoformat(),
        "user_message": msg.message,
        "response": matched_response["response"],
        "category": matched_response["category"],
        "topic": matched_topic,
        "confidence": round(random.uniform(0.85, 0.98), 2) if matched_topic != "general" else round(random.uniform(0.65, 0.80), 2),
        "related_features": _get_related_features(matched_topic),
    }


@router.get("/suggestions")
async def get_suggestions():
    """Get suggested prompts for the chat assistant."""
    return {
        "suggestions": [
            {"text": "What is a force majeure clause?", "category": "Clauses", "icon": "⚡"},
            {"text": "Explain NDA types and best practices", "category": "Agreements", "icon": "🔒"},
            {"text": "What are GDPR requirements for contracts?", "category": "Compliance", "icon": "🇪🇺"},
            {"text": "How should I draft an indemnification clause?", "category": "Drafting", "icon": "🛡️"},
            {"text": "What makes a termination clause effective?", "category": "Clauses", "icon": "⏹️"},
            {"text": "Explain intellectual property assignment", "category": "IP", "icon": "💡"},
            {"text": "What is a limitation of liability clause?", "category": "Risk", "icon": "⚖️"},
            {"text": "How to handle dispute resolution clauses?", "category": "Disputes", "icon": "🤝"},
        ]
    }


def _get_related_features(topic: str) -> list[dict]:
    """Suggest related features based on topic."""
    features = {
        "force majeure": [
            {"name": "Clause Library", "path": "/clauses", "description": "Browse force majeure clause templates"},
            {"name": "Risk Analysis", "path": "/risk-analysis", "description": "Analyze risk impact"},
        ],
        "nda": [
            {"name": "Template Library", "path": "/templates", "description": "Browse NDA templates"},
            {"name": "Generate Contract", "path": "/generate", "description": "Generate a new NDA"},
        ],
        "gdpr": [
            {"name": "Compliance Center", "path": "/compliance", "description": "Run GDPR compliance check"},
            {"name": "Clause Library", "path": "/clauses", "description": "Browse GDPR-related clauses"},
        ],
        "indemnification": [
            {"name": "Risk Analysis", "path": "/risk-analysis", "description": "Analyze indemnification risk"},
            {"name": "Clause Library", "path": "/clauses", "description": "Browse indemnification clauses"},
        ],
        "termination": [
            {"name": "Clause Library", "path": "/clauses", "description": "Browse termination clauses"},
            {"name": "Calendar", "path": "/calendar", "description": "Track contract deadlines"},
        ],
    }
    return features.get(topic, [
        {"name": "Clause Library", "path": "/clauses", "description": "Browse legal clause templates"},
        {"name": "Risk Analysis", "path": "/risk-analysis", "description": "Analyze contract risk"},
    ])
