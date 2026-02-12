"""Template Engine Service - Dynamic contract template management."""

import re
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import structlog
from jinja2 import Environment, BaseLoader, TemplateSyntaxError

from app.config import settings

logger = structlog.get_logger(__name__)


# ─── Contract Templates ─────────────────────────────────────────────────

CONTRACT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "nda": {
        "name": "Non-Disclosure Agreement",
        "description": "Mutual or unilateral NDA for protecting confidential information",
        "complexity": "simple",
        "variables": [
            "disclosing_party_name", "disclosing_party_type", "disclosing_party_address",
            "receiving_party_name", "receiving_party_type", "receiving_party_address",
            "purpose", "term_years", "survival_years", "governing_law_state",
            "is_mutual", "effective_date",
        ],
        "clause_structure": [
            "definitions", "obligations", "exclusions", "term_and_termination",
            "return_of_materials", "remedies", "governing_law", "general_provisions",
        ],
    },
    "msa": {
        "name": "Master Service Agreement",
        "description": "Comprehensive service agreement with SOW framework",
        "complexity": "complex",
        "variables": [
            "client_name", "client_type", "client_address",
            "provider_name", "provider_type", "provider_address",
            "service_description", "payment_terms", "term_years",
            "liability_cap", "sla_uptime", "governing_law_state",
            "insurance_requirements", "data_handling_terms",
        ],
        "clause_structure": [
            "definitions", "scope_of_services", "service_levels",
            "payment_terms", "intellectual_property", "confidentiality",
            "representations_warranties", "indemnification", "limitation_of_liability",
            "insurance", "term_and_termination", "data_protection",
            "force_majeure", "dispute_resolution", "general_provisions",
        ],
    },
    "employment": {
        "name": "Employment Agreement",
        "description": "Standard employment contract with benefits and restrictions",
        "complexity": "standard",
        "variables": [
            "employer_name", "employer_type", "employer_address",
            "employee_name", "employee_address",
            "position_title", "department", "start_date",
            "salary", "pay_frequency", "benefits",
            "vacation_days", "probation_period_months",
            "non_compete_months", "non_compete_radius_miles",
            "governing_law_state",
        ],
        "clause_structure": [
            "position_and_duties", "compensation_and_benefits",
            "work_schedule", "confidentiality", "intellectual_property",
            "non_compete", "non_solicitation", "termination",
            "severance", "governing_law", "general_provisions",
        ],
    },
    "service_agreement": {
        "name": "Service Agreement",
        "description": "Agreement for provision of professional services",
        "complexity": "standard",
        "variables": [
            "client_name", "client_type", "client_address",
            "provider_name", "provider_type", "provider_address",
            "service_description", "deliverables",
            "start_date", "end_date", "total_fee",
            "payment_schedule", "governing_law_state",
        ],
        "clause_structure": [
            "scope_of_services", "deliverables", "timeline",
            "compensation", "expenses", "independent_contractor",
            "confidentiality", "intellectual_property",
            "representations_warranties", "indemnification",
            "limitation_of_liability", "termination",
            "governing_law", "general_provisions",
        ],
    },
    "license": {
        "name": "Software License Agreement",
        "description": "Software licensing with usage rights and restrictions",
        "complexity": "standard",
        "variables": [
            "licensor_name", "licensor_type", "licensor_address",
            "licensee_name", "licensee_type", "licensee_address",
            "software_name", "license_type", "license_scope",
            "license_fee", "payment_terms", "term_years",
            "user_limit", "support_level", "governing_law_state",
        ],
        "clause_structure": [
            "definitions", "grant_of_license", "license_restrictions",
            "fees_and_payment", "support_and_maintenance",
            "intellectual_property", "confidentiality",
            "warranties", "limitation_of_liability",
            "term_and_termination", "data_protection",
            "governing_law", "general_provisions",
        ],
    },
    "partnership": {
        "name": "Partnership Agreement",
        "description": "Business partnership formation and governance",
        "complexity": "complex",
        "variables": [
            "partnership_name", "business_purpose",
            "partner_details",  # List of partner info
            "capital_contributions", "profit_sharing_ratio",
            "management_structure", "fiscal_year_end",
            "term_years", "governing_law_state",
        ],
        "clause_structure": [
            "formation", "purpose", "capital_contributions",
            "profit_and_loss", "management_and_voting",
            "partner_duties", "distributions",
            "admission_of_new_partners", "withdrawal_and_removal",
            "dissolution", "non_compete", "confidentiality",
            "dispute_resolution", "general_provisions",
        ],
    },
    "merger_acquisition": {
        "name": "Merger & Acquisition Agreement",
        "description": "M&A transaction with representations, warranties, and closing conditions",
        "complexity": "complex",
        "variables": [
            "buyer_name", "buyer_type", "buyer_address",
            "seller_name", "seller_type", "seller_address",
            "target_company", "purchase_price", "payment_structure",
            "closing_date", "escrow_amount", "escrow_period",
            "non_compete_years", "governing_law_state",
        ],
        "clause_structure": [
            "definitions", "purchase_and_sale", "purchase_price",
            "closing_conditions", "representations_warranties_seller",
            "representations_warranties_buyer", "covenants",
            "indemnification", "non_compete", "confidentiality",
            "termination", "survival", "governing_law", "general_provisions",
        ],
    },
    "lease": {
        "name": "Commercial Lease Agreement",
        "description": "Commercial property lease with detailed terms",
        "complexity": "standard",
        "variables": [
            "landlord_name", "landlord_type", "landlord_address",
            "tenant_name", "tenant_type", "tenant_address",
            "property_address", "property_description",
            "lease_term_years", "monthly_rent", "security_deposit",
            "permitted_use", "maintenance_responsibility",
            "insurance_requirements", "governing_law_state",
        ],
        "clause_structure": [
            "premises", "term", "rent", "security_deposit",
            "permitted_use", "maintenance_and_repairs",
            "insurance", "indemnification", "assignment_and_subletting",
            "default_and_remedies", "termination",
            "governing_law", "general_provisions",
        ],
    },
}


# ─── Clause Templates ───────────────────────────────────────────────────

CLAUSE_TEMPLATES: Dict[str, str] = {
    "definitions": """
ARTICLE {{ clause_number }}. DEFINITIONS

{{ clause_number }}.1 "Agreement" means this {{ contract_type_name }} and all exhibits, 
schedules, and amendments attached hereto or incorporated by reference.

{{ clause_number }}.2 "Affiliate" means any entity that directly or indirectly controls, 
is controlled by, or is under common control with a Party, where "control" means ownership 
of more than fifty percent (50%) of the voting securities.

{{ clause_number }}.3 "Business Day" means any day other than a Saturday, Sunday, or public 
holiday in {{ governing_law_state }}.

{{ clause_number }}.4 "Confidential Information" means any information designated as 
confidential or that reasonably should be understood to be confidential given the nature 
of the information and circumstances of disclosure.

{{ additional_definitions }}
""",

    "confidentiality": """
ARTICLE {{ clause_number }}. CONFIDENTIALITY

{{ clause_number }}.1 Obligations. Each Party receiving Confidential Information 
("Receiving Party") from the other Party ("Disclosing Party") shall:

(a) hold such Confidential Information in strict confidence;
(b) not disclose such Confidential Information to any third party without the prior 
    written consent of the Disclosing Party;
(c) use such Confidential Information solely for the purposes contemplated by this Agreement;
(d) protect such Confidential Information using the same degree of care it uses to protect 
    its own confidential information, but in no event less than reasonable care.

{{ clause_number }}.2 Exceptions. The obligations set forth in Section {{ clause_number }}.1 
shall not apply to information that:

(a) is or becomes publicly available through no fault of the Receiving Party;
(b) was known to the Receiving Party prior to disclosure;
(c) is independently developed by the Receiving Party;
(d) is rightfully obtained from a third party without restriction;
(e) is required to be disclosed by law, regulation, or court order, provided that the 
    Receiving Party gives the Disclosing Party prompt notice and cooperates in seeking 
    a protective order.

{{ clause_number }}.3 Duration. The obligations of confidentiality shall survive 
{{ survival_years | default("five (5)") }} years following the termination or expiration 
of this Agreement.
""",

    "indemnification": """
ARTICLE {{ clause_number }}. INDEMNIFICATION

{{ clause_number }}.1 Indemnification by {{ indemnifying_party | default("Each Party") }}. 
{{ indemnifying_party | default("Each Party") }} (the "Indemnifying Party") shall defend, 
indemnify, and hold harmless the other Party and its Affiliates, directors, officers, 
employees, and agents (collectively, "Indemnified Parties") from and against any and all 
claims, damages, losses, liabilities, costs, and expenses (including reasonable attorneys' 
fees) ("Losses") arising out of or related to:

(a) the Indemnifying Party's material breach of this Agreement;
(b) the Indemnifying Party's negligence or willful misconduct;
(c) any violation of applicable law by the Indemnifying Party;
{% if include_ip_indemnity %}
(d) any claim that the Indemnifying Party's deliverables or materials infringe any 
    third-party intellectual property right;
{% endif %}

{{ clause_number }}.2 Indemnification Procedures. The Indemnified Party shall:
(a) promptly notify the Indemnifying Party of any claim;
(b) grant the Indemnifying Party sole control of the defense and settlement;
(c) provide reasonable cooperation at the Indemnifying Party's expense.

{{ clause_number }}.3 Limitations. The Indemnifying Party shall not settle any claim 
without the Indemnified Party's prior written consent if such settlement imposes any 
obligation on the Indemnified Party or does not unconditionally release the Indemnified Party.
""",

    "limitation_of_liability": """
ARTICLE {{ clause_number }}. LIMITATION OF LIABILITY

{{ clause_number }}.1 Limitation of Damages. EXCEPT FOR OBLIGATIONS UNDER ARTICLE 
[INDEMNIFICATION] AND BREACHES OF CONFIDENTIALITY OBLIGATIONS, IN NO EVENT SHALL 
EITHER PARTY BE LIABLE TO THE OTHER PARTY FOR ANY INDIRECT, INCIDENTAL, SPECIAL, 
CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO LOSS OF PROFITS, 
REVENUE, DATA, OR BUSINESS OPPORTUNITY, REGARDLESS OF THE THEORY OF LIABILITY.

{{ clause_number }}.2 Cap on Liability. EXCEPT FOR OBLIGATIONS UNDER ARTICLE 
[INDEMNIFICATION], EACH PARTY'S TOTAL AGGREGATE LIABILITY ARISING OUT OF OR RELATED 
TO THIS AGREEMENT SHALL NOT EXCEED {{ liability_cap | default("THE TOTAL FEES PAID OR PAYABLE UNDER THIS AGREEMENT DURING THE TWELVE (12) MONTHS PRECEDING THE CLAIM") }}.

{{ clause_number }}.3 Essential Basis. THE LIMITATIONS SET FORTH IN THIS ARTICLE REFLECT 
THE ALLOCATION OF RISK BETWEEN THE PARTIES AND FORM AN ESSENTIAL BASIS OF THE BARGAIN 
BETWEEN THEM.
""",

    "governing_law": """
ARTICLE {{ clause_number }}. GOVERNING LAW AND DISPUTE RESOLUTION

{{ clause_number }}.1 Governing Law. This Agreement shall be governed by and construed 
in accordance with the laws of {{ governing_law_state }}, without giving effect to any 
choice or conflict of law provision or rule.

{{ clause_number }}.2 Dispute Resolution. 
{% if dispute_mechanism == "arbitration" %}
Any dispute arising out of or relating to this Agreement shall be finally resolved by 
binding arbitration administered by the American Arbitration Association ("AAA") under 
its Commercial Arbitration Rules. The arbitration shall be conducted by 
{{ arbitrator_count | default("one (1)") }} arbitrator(s) in {{ arbitration_venue }}. 
The arbitrator's decision shall be final and binding, and judgment upon the award may 
be entered in any court having jurisdiction.
{% elif dispute_mechanism == "mediation_then_arbitration" %}
The Parties shall first attempt to resolve any dispute through good faith negotiation. 
If unresolved within thirty (30) days, the Parties shall submit the dispute to mediation 
under the AAA Mediation Rules. If mediation is unsuccessful within sixty (60) days, the 
dispute shall be resolved by binding arbitration as provided in Section {{ clause_number }}.2.
{% else %}
Any legal action arising out of or relating to this Agreement shall be brought exclusively 
in the federal or state courts located in {{ court_venue | default(governing_law_state) }}, 
and each Party consents to the personal jurisdiction of such courts.
{% endif %}

{{ clause_number }}.3 Attorneys' Fees. The prevailing Party in any action to enforce this 
Agreement shall be entitled to recover reasonable attorneys' fees and costs.
""",

    "term_and_termination": """
ARTICLE {{ clause_number }}. TERM AND TERMINATION

{{ clause_number }}.1 Term. This Agreement shall commence on the Effective Date and 
continue for a period of {{ term_years | default("one (1)") }} year(s) (the "Initial Term"), 
unless earlier terminated as provided herein.

{{ clause_number }}.2 Renewal. {{ renewal_terms | default("This Agreement shall automatically renew for successive one (1) year periods unless either Party provides written notice of non-renewal at least sixty (60) days prior to the end of the then-current term.") }}

{{ clause_number }}.3 Termination for Convenience. Either Party may terminate this Agreement 
upon {{ notice_period | default("thirty (30)") }} days' prior written notice to the other Party.

{{ clause_number }}.4 Termination for Cause. Either Party may terminate this Agreement 
immediately upon written notice if the other Party:

(a) materially breaches this Agreement and fails to cure such breach within 
    {{ cure_period | default("thirty (30)") }} days after receiving written notice;
(b) becomes insolvent, files for bankruptcy, or has a receiver appointed for its assets;
(c) ceases to conduct business in the normal course.

{{ clause_number }}.5 Effect of Termination. Upon termination or expiration:

(a) all rights and licenses granted hereunder shall immediately terminate;
(b) each Party shall return or destroy all Confidential Information of the other Party;
(c) any accrued rights, obligations, and liabilities shall survive termination;
(d) Sections [CONFIDENTIALITY], [INDEMNIFICATION], [LIMITATION OF LIABILITY], and 
    [GOVERNING LAW] shall survive termination.
""",

    "force_majeure": """
ARTICLE {{ clause_number }}. FORCE MAJEURE

{{ clause_number }}.1 Neither Party shall be liable for any failure or delay in performing 
its obligations under this Agreement (except for payment obligations) to the extent that 
such failure or delay results from circumstances beyond the Party's reasonable control, 
including but not limited to: acts of God, natural disasters, epidemics or pandemics, 
war, terrorism, riots, government actions, power failures, internet or telecommunications 
failures, or any other cause beyond the reasonable control of the affected Party 
(each, a "Force Majeure Event").

{{ clause_number }}.2 The affected Party shall:
(a) promptly notify the other Party of the Force Majeure Event;
(b) use commercially reasonable efforts to mitigate and overcome the effects; and
(c) resume performance as soon as reasonably practicable.

{{ clause_number }}.3 If a Force Majeure Event continues for more than 
{{ force_majeure_termination_days | default("ninety (90)") }} consecutive days, either 
Party may terminate this Agreement upon written notice without liability.
""",

    "data_protection": """
ARTICLE {{ clause_number }}. DATA PROTECTION

{{ clause_number }}.1 Compliance. Each Party shall comply with all applicable data 
protection laws and regulations, including but not limited to the General Data Protection 
Regulation (EU) 2016/679 ("GDPR"), the California Consumer Privacy Act ("CCPA"), and the 
Health Insurance Portability and Accountability Act ("HIPAA"), as applicable.

{{ clause_number }}.2 Data Processing. Where a Party processes personal data on behalf of 
the other Party, the processing Party shall:

(a) process personal data only in accordance with documented instructions;
(b) ensure that persons authorized to process personal data are bound by confidentiality;
(c) implement appropriate technical and organizational security measures;
(d) not engage sub-processors without prior written authorization;
(e) assist the other Party in responding to data subject requests;
(f) delete or return all personal data upon termination;
(g) make available all information necessary to demonstrate compliance.

{{ clause_number }}.3 Data Breach. In the event of a personal data breach, the affected 
Party shall notify the other Party without undue delay and in any event within 
{{ breach_notification_hours | default("seventy-two (72)") }} hours of becoming aware 
of the breach.

{{ clause_number }}.4 International Transfers. Any transfer of personal data to a country 
outside the European Economic Area shall be subject to appropriate safeguards as required 
by applicable data protection law.
""",

    "intellectual_property": """
ARTICLE {{ clause_number }}. INTELLECTUAL PROPERTY

{{ clause_number }}.1 Ownership. 
{% if ip_ownership == "client" %}
All intellectual property rights in the deliverables and work product created under 
this Agreement shall be owned exclusively by {{ client_name }}. {{ provider_name }} 
hereby assigns all right, title, and interest in such work product to {{ client_name }}.
{% elif ip_ownership == "provider" %}
All intellectual property rights in pre-existing materials and proprietary tools shall 
remain with {{ provider_name }}. {{ provider_name }} grants {{ client_name }} a 
non-exclusive, perpetual license to use the deliverables for internal business purposes.
{% else %}
Each Party retains all rights in its pre-existing intellectual property. Any jointly 
developed intellectual property shall be jointly owned by the Parties.
{% endif %}

{{ clause_number }}.2 License. {{ provider_name | default("Provider") }} grants 
{{ client_name | default("Client") }} a non-exclusive, worldwide, royalty-free license 
to use any pre-existing intellectual property of {{ provider_name }} solely to the extent 
incorporated in the deliverables and necessary for {{ client_name }}'s use thereof.

{{ clause_number }}.3 No Infringement. Each Party represents and warrants that its 
performance under this Agreement and the deliverables provided hereunder shall not 
infringe any third-party intellectual property rights.
""",

    "general_provisions": """
ARTICLE {{ clause_number }}. GENERAL PROVISIONS

{{ clause_number }}.1 Entire Agreement. This Agreement, together with all exhibits and 
schedules, constitutes the entire agreement between the Parties with respect to the subject 
matter hereof and supersedes all prior negotiations, representations, warranties, 
commitments, offers, contracts, and agreements, whether written or oral.

{{ clause_number }}.2 Amendment. No amendment, modification, or waiver of any provision 
of this Agreement shall be effective unless in writing and signed by both Parties.

{{ clause_number }}.3 Waiver. No waiver of any right or remedy hereunder shall be effective 
unless in writing. No waiver of any breach shall constitute a waiver of any subsequent breach.

{{ clause_number }}.4 Severability. If any provision of this Agreement is held to be invalid, 
illegal, or unenforceable, the validity, legality, and enforceability of the remaining 
provisions shall not be affected.

{{ clause_number }}.5 Assignment. Neither Party may assign or transfer this Agreement or 
any rights or obligations hereunder without the prior written consent of the other Party, 
except in connection with a merger, acquisition, or sale of all or substantially all of 
the assigning Party's assets.

{{ clause_number }}.6 Notices. All notices required or permitted under this Agreement shall 
be in writing and delivered by certified mail (return receipt requested), nationally 
recognized overnight courier, or email (with confirmation of receipt) to the addresses 
specified in this Agreement.

{{ clause_number }}.7 Independent Contractors. The Parties are independent contractors. 
Nothing in this Agreement creates a partnership, joint venture, agency, or employment 
relationship between the Parties.

{{ clause_number }}.8 Counterparts. This Agreement may be executed in counterparts, 
including electronic counterparts, each of which shall be deemed an original, and all 
of which together shall constitute one and the same instrument.

{{ clause_number }}.9 Headings. Section headings are for convenience only and shall not 
affect the interpretation of this Agreement.
""",
}


# ─── Template Engine Service ────────────────────────────────────────────

class TemplateEngine:
    """Service for managing and rendering contract templates."""

    def __init__(self):
        self.jinja_env = Environment(loader=BaseLoader())
        self.templates = CONTRACT_TEMPLATES
        self.clause_templates = CLAUSE_TEMPLATES

    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available contract templates."""
        return [
            {
                "id": key,
                "name": value["name"],
                "description": value["description"],
                "complexity": value["complexity"],
                "required_variables": value["variables"],
                "clause_count": len(value["clause_structure"]),
            }
            for key, value in self.templates.items()
        ]

    def list_templates(self) -> List[Dict[str, Any]]:
        """Alias for get_available_templates (route compatibility)."""
        return self.get_available_templates()

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID."""
        return self.templates.get(template_id)

    def get_template_variables(self, template_id: str) -> List[str]:
        """Get required variables for a template."""
        template = self.templates.get(template_id)
        if not template:
            return []
        return template["variables"]

    def render_clause(
        self,
        clause_type: str,
        variables: Dict[str, Any],
    ) -> str:
        """Render a specific clause template with variables."""
        template_str = self.clause_templates.get(clause_type, "")
        if not template_str:
            return ""

        try:
            template = self.jinja_env.from_string(template_str)
            return template.render(**variables)
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error in {clause_type}: {e}")
            return f"[Error rendering {clause_type} clause]"

    def build_contract_from_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
    ) -> str:
        """Build a complete contract from a template and variables."""
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        contract_parts = []
        contract_type_name = template["name"]

        # Header
        effective_date = variables.get("effective_date", datetime.now(timezone.utc).strftime("%B %d, %Y"))
        contract_parts.append(f"""
{'=' * 80}
{contract_type_name.upper()}
{'=' * 80}

THIS {contract_type_name.upper()} (this "Agreement") is entered into as of 
{effective_date} (the "Effective Date"),

BETWEEN:
""")

        # Add party information
        party_fields = self._extract_party_info(template_id, variables)
        for party in party_fields:
            contract_parts.append(f"""
{party['name']}, a {party['type']} organized under the laws of 
{party.get('jurisdiction', variables.get('governing_law_state', 'the applicable jurisdiction'))}, 
with its principal place of business at {party['address']} ("{party['role']}");
""")

        contract_parts.append("\n(each a \"Party\" and collectively the \"Parties\").\n")

        # Build clauses
        clause_structure = template["clause_structure"]
        for i, clause_type in enumerate(clause_structure, 1):
            clause_vars = {**variables, "clause_number": str(i), "contract_type_name": contract_type_name}
            rendered_clause = self.render_clause(clause_type, clause_vars)
            if rendered_clause:
                contract_parts.append(rendered_clause)

        # Signature block
        contract_parts.append(self._generate_signature_block(template_id, variables))

        return "\n".join(contract_parts)

    def _extract_party_info(self, template_id: str, variables: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract party information from variables based on template type."""
        parties = []

        party_mappings = {
            "nda": [
                ("disclosing_party", "Disclosing Party"),
                ("receiving_party", "Receiving Party"),
            ],
            "msa": [
                ("client", "Client"),
                ("provider", "Service Provider"),
            ],
            "employment": [
                ("employer", "Employer"),
                ("employee", "Employee"),
            ],
            "service_agreement": [
                ("client", "Client"),
                ("provider", "Service Provider"),
            ],
            "license": [
                ("licensor", "Licensor"),
                ("licensee", "Licensee"),
            ],
            "partnership": [
                ("partner_1", "Partner"),
                ("partner_2", "Partner"),
            ],
            "merger_acquisition": [
                ("buyer", "Buyer"),
                ("seller", "Seller"),
            ],
            "lease": [
                ("landlord", "Landlord"),
                ("tenant", "Tenant"),
            ],
        }

        mappings = party_mappings.get(template_id, [])
        for prefix, role in mappings:
            parties.append({
                "name": variables.get(f"{prefix}_name", f"[{role.upper()} NAME]"),
                "type": variables.get(f"{prefix}_type", "entity"),
                "address": variables.get(f"{prefix}_address", f"[{role.upper()} ADDRESS]"),
                "role": role,
                "jurisdiction": variables.get(f"{prefix}_jurisdiction", ""),
            })

        return parties

    def _generate_signature_block(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Generate signature block for the contract."""
        parties = self._extract_party_info(template_id, variables)

        block = "\n\nIN WITNESS WHEREOF, the Parties have executed this Agreement as of the Effective Date.\n\n"

        for party in parties:
            block += f"""
{party['name']}

By: ________________________________
Name: ______________________________
Title: _____________________________
Date: ______________________________

"""

        return block

    def suggest_clauses(
        self,
        contract_type: str,
        risk_profile: str = "standard",
        industry: str = "general",
    ) -> List[Dict[str, str]]:
        """Suggest clauses based on contract type and risk profile."""
        suggestions = []

        # Base clauses for all contracts
        base_clauses = [
            "definitions", "confidentiality", "term_and_termination",
            "governing_law", "general_provisions",
        ]

        # Additional clauses based on risk profile
        if risk_profile in ("high", "critical"):
            base_clauses.extend([
                "indemnification", "limitation_of_liability",
                "force_majeure", "data_protection",
            ])

        # Industry-specific clauses
        industry_clauses = {
            "healthcare": ["hipaa_compliance", "data_protection", "audit_rights"],
            "fintech": ["regulatory_compliance", "data_protection", "audit_rights"],
            "technology": ["intellectual_property", "data_protection", "sla"],
        }

        if industry in industry_clauses:
            base_clauses.extend(industry_clauses[industry])

        for clause_type in list(dict.fromkeys(base_clauses)):  # Deduplicate preserving order
            if clause_type in self.clause_templates:
                suggestions.append({
                    "type": clause_type,
                    "name": clause_type.replace("_", " ").title(),
                    "available": True,
                })
            else:
                suggestions.append({
                    "type": clause_type,
                    "name": clause_type.replace("_", " ").title(),
                    "available": False,
                })

        return suggestions

    def validate_template_variables(
        self,
        template_id: str,
        provided_variables: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate that all required variables are provided."""
        template = self.templates.get(template_id)
        if not template:
            return {"valid": False, "error": f"Template '{template_id}' not found"}

        required = set(template["variables"])
        provided = set(provided_variables.keys())
        missing = required - provided

        return {
            "valid": len(missing) == 0,
            "missing_variables": list(missing),
            "extra_variables": list(provided - required),
            "total_required": len(required),
            "total_provided": len(provided),
        }


# Singleton instance
template_engine = TemplateEngine()
