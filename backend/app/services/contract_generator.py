"""Contract Generation Service - End-to-end contract creation engine."""

import uuid
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import structlog

from app.config import settings
from app.core.security import hash_document, encrypt_data
from app.core.exceptions import (
    ContractGenerationError, TemplateNotFoundError, ContractValidationError
)
from app.services.llm_service import llm_service
from app.services.template_engine import template_engine

logger = structlog.get_logger(__name__)


# ─── Pydantic Schemas for Contract Generation ───────────────────────────

from pydantic import BaseModel, Field
from typing import Literal


class PartyInfo(BaseModel):
    """Information about a contract party."""
    name: str = Field(..., description="Legal name of the party")
    role: str = Field(..., description="Role in the contract (e.g., 'Disclosing Party')")
    entity_type: str = Field(default="corporation", description="Type of entity")
    jurisdiction: Optional[str] = None
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    signing_authority: Optional[str] = None


class ContractGenerationRequest(BaseModel):
    """Request schema for contract generation."""
    contract_type: str = Field(..., description="Type of contract to generate")
    parties: List[PartyInfo] = Field(..., min_length=2, description="Parties to the contract")
    jurisdiction: str = Field(..., description="Primary jurisdiction")
    governing_law: Optional[str] = Field(None, description="Governing law jurisdiction")
    language: str = Field(default="en", description="Contract language")
    key_terms: Dict[str, Any] = Field(default_factory=dict, description="Key contract terms")
    special_requirements: Optional[str] = Field(None, description="Special requirements or instructions")
    industry: str = Field(default="general", description="Industry context")
    use_template: bool = Field(default=True, description="Whether to use template system")
    template_id: Optional[str] = Field(None, description="Specific template ID to use")
    risk_level: str = Field(default="standard", description="Desired risk protection level")
    include_data_protection: bool = Field(default=True)
    include_force_majeure: bool = Field(default=True)
    llm_provider: Optional[str] = Field(None, description="Specific LLM provider to use")


class ContractGenerationResponse(BaseModel):
    """Response schema for generated contracts."""
    contract_id: str
    title: str
    contract_type: str
    content: str
    content_hash: str
    jurisdiction: str
    language: str
    clauses: List[Dict[str, Any]]
    parties: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    generation_time_ms: int
    confidence_score: float
    template_used: Optional[str]
    model_used: str


# ─── Contract Generation Engine ─────────────────────────────────────────

class ContractGenerator:
    """Service for generating legal contracts."""

    def __init__(self):
        self.llm = llm_service
        self.templates = template_engine

    async def generate_contract(
        self,
        request: ContractGenerationRequest,
    ) -> ContractGenerationResponse:
        """Generate a complete legal contract."""
        start_time = time.time()
        contract_id = str(uuid.uuid4())

        logger.info(
            "Starting contract generation",
            contract_id=contract_id,
            contract_type=request.contract_type,
            jurisdiction=request.jurisdiction,
        )

        try:
            # Step 1: Validate request
            self._validate_request(request)

            # Step 2: Generate content
            if request.use_template and request.contract_type in self.templates.templates:
                content = await self._generate_from_template(request)
            else:
                content = await self._generate_from_llm(request)

            # Step 3: Post-process content
            content = self._post_process_content(content, request)

            # Step 4: Extract clauses
            clauses = self._extract_clauses(content)

            # Step 5: Validate legal accuracy
            validation_result = self._validate_contract(content, request)

            # Step 6: Calculate content hash
            content_hash = hash_document(content)

            generation_time = int((time.time() - start_time) * 1000)

            # Build response
            title = self._generate_title(request)
            parties_data = [p.model_dump() for p in request.parties]

            response = ContractGenerationResponse(
                contract_id=contract_id,
                title=title,
                contract_type=request.contract_type,
                content=content,
                content_hash=content_hash,
                jurisdiction=request.jurisdiction,
                language=request.language,
                clauses=clauses,
                parties=parties_data,
                metadata={
                    "generation_method": "template" if request.use_template else "llm",
                    "template_id": request.template_id,
                    "key_terms": request.key_terms,
                    "special_requirements": request.special_requirements,
                    "validation": validation_result,
                    "risk_level": request.risk_level,
                    "industry": request.industry,
                },
                generation_time_ms=generation_time,
                confidence_score=validation_result.get("confidence", 0.95),
                template_used=request.template_id or request.contract_type,
                model_used=request.llm_provider or settings.DEFAULT_LLM_PROVIDER,
            )

            logger.info(
                "Contract generation completed",
                contract_id=contract_id,
                generation_time_ms=generation_time,
                clause_count=len(clauses),
            )

            return response

        except (TemplateNotFoundError, ContractValidationError):
            raise
        except Exception as e:
            logger.error(
                "Contract generation failed",
                contract_id=contract_id,
                error=str(e),
            )
            raise ContractGenerationError(
                f"Failed to generate contract: {str(e)}",
                details={"contract_type": request.contract_type, "jurisdiction": request.jurisdiction},
            )

    def _validate_request(self, request: ContractGenerationRequest):
        """Validate the generation request."""
        # Validate jurisdiction
        if request.jurisdiction not in settings.SUPPORTED_JURISDICTIONS:
            raise ContractValidationError(
                f"Jurisdiction '{request.jurisdiction}' is not supported",
                validation_errors=[{
                    "field": "jurisdiction",
                    "error": f"Must be one of: {', '.join(settings.SUPPORTED_JURISDICTIONS[:10])}...",
                }],
            )

        # Validate parties
        if len(request.parties) < 2:
            raise ContractValidationError(
                "At least two parties are required",
                validation_errors=[{"field": "parties", "error": "Minimum 2 parties required"}],
            )

        # Validate contract type
        valid_types = [
            "nda", "msa", "employment", "consulting", "license", "partnership",
            "real_estate", "merger_acquisition", "service_agreement", "purchase_order",
            "lease", "loan", "supply", "distribution", "franchise", "joint_venture",
            "settlement", "custom",
        ]
        if request.contract_type not in valid_types:
            raise ContractValidationError(
                f"Invalid contract type: {request.contract_type}",
                validation_errors=[{"field": "contract_type", "error": f"Must be one of: {', '.join(valid_types)}"}],
            )

    async def _generate_from_template(
        self,
        request: ContractGenerationRequest,
    ) -> str:
        """Generate contract using template engine."""
        template_id = request.template_id or request.contract_type

        # Build template variables from request
        variables = {**request.key_terms}
        variables["governing_law_state"] = request.governing_law or request.jurisdiction
        variables["effective_date"] = request.key_terms.get(
            "effective_date",
            datetime.now(timezone.utc).strftime("%B %d, %Y"),
        )

        # Map party info to template variables
        for i, party in enumerate(request.parties):
            prefix = self._get_party_prefix(request.contract_type, i)
            variables[f"{prefix}_name"] = party.name
            variables[f"{prefix}_type"] = party.entity_type
            variables[f"{prefix}_address"] = party.address or "[ADDRESS]"
            if party.jurisdiction:
                variables[f"{prefix}_jurisdiction"] = party.jurisdiction

        # Additional variables
        variables["include_ip_indemnity"] = request.industry in ("technology", "software", "media")
        variables["dispute_mechanism"] = request.key_terms.get("dispute_mechanism", "arbitration")
        variables["ip_ownership"] = request.key_terms.get("ip_ownership", "shared")

        try:
            content = self.templates.build_contract_from_template(template_id, variables)

            # Enhance with LLM if content is too short or needs improvement
            if len(content) < 2000:
                content = await self._enhance_with_llm(content, request)

            return content
        except ValueError as e:
            raise TemplateNotFoundError(template_id)

    async def _generate_from_llm(self, request: ContractGenerationRequest) -> str:
        """Generate contract entirely using LLM."""
        parties_data = [
            {
                "name": p.name,
                "role": p.role,
                "type": p.entity_type,
            }
            for p in request.parties
        ]

        content = await self.llm.generate_contract(
            contract_type=request.contract_type,
            parties=parties_data,
            jurisdiction=request.jurisdiction,
            governing_law=request.governing_law or request.jurisdiction,
            key_terms=request.key_terms,
            special_requirements=request.special_requirements or "",
            industry=request.industry,
            language=request.language,
            provider=request.llm_provider,
        )

        return content

    async def _enhance_with_llm(self, template_content: str, request: ContractGenerationRequest) -> str:
        """Enhance template-generated content with LLM refinement."""
        prompt = f"""Review and enhance the following contract draft. 
Ensure all provisions are legally sound for {request.jurisdiction} jurisdiction.
Add any missing standard clauses for a {request.contract_type} agreement.
Maintain the existing structure but improve language precision.

Contract Draft:
{template_content}

Special Requirements: {request.special_requirements or 'None'}
Industry: {request.industry}

Return the improved complete contract."""

        try:
            enhanced = await self.llm.get_provider(request.llm_provider).generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            return enhanced if len(enhanced) > len(template_content) * 0.8 else template_content
        except Exception as e:
            logger.warning(f"LLM enhancement failed, using template content: {e}")
            return template_content

    def _post_process_content(self, content: str, request: ContractGenerationRequest) -> str:
        """Post-process generated contract content."""
        import re

        # Clean up excessive whitespace
        content = re.sub(r'\n{4,}', '\n\n\n', content)

        # Ensure proper formatting
        content = content.strip()

        # Add header if missing
        if not content.startswith(("=", "THIS", "MUTUAL", "#")):
            contract_name = request.contract_type.replace("_", " ").upper()
            content = f"{'=' * 80}\n{contract_name}\n{'=' * 80}\n\n{content}"

        return content

    def _extract_clauses(self, content: str) -> List[Dict[str, Any]]:
        """Extract individual clauses from contract content."""
        import re

        clauses = []
        # Match patterns like "ARTICLE 1.", "Section 1.", "1.", "1.1"
        patterns = [
            r'(?:ARTICLE|Section|SECTION)\s+(\d+\.?\d*)\.\s*([A-Z][A-Z\s&]+)',
            r'^(\d+\.)\s*([A-Z][A-Z\s&]+)',
            r'\[([A-Z_]+)\]\s*(\d+\.)\s*([A-Z][A-Z\s&]+)',
        ]

        lines = content.split('\n')
        current_clause = None
        current_content = []

        for line in lines:
            matched = False
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    # Save previous clause
                    if current_clause:
                        current_clause["content"] = "\n".join(current_content).strip()
                        if current_clause["content"]:
                            clauses.append(current_clause)

                    groups = match.groups()
                    clause_number = groups[0] if len(groups) >= 1 else str(len(clauses) + 1)
                    title = groups[-1] if len(groups) >= 2 else "Untitled"

                    # Detect clause type from brackets or title
                    clause_type = self._detect_clause_type(line, title)

                    current_clause = {
                        "clause_number": clause_number.strip("."),
                        "title": title.strip(),
                        "clause_type": clause_type,
                        "risk_score": 0.0,
                        "is_standard": True,
                    }
                    current_content = [line]
                    matched = True
                    break

            if not matched and current_clause:
                current_content.append(line)

        # Add last clause
        if current_clause:
            current_clause["content"] = "\n".join(current_content).strip()
            if current_clause["content"]:
                clauses.append(current_clause)

        return clauses

    def _detect_clause_type(self, line: str, title: str) -> str:
        """Detect the type of a clause from its content."""
        import re

        # Check for bracket annotations [TYPE]
        bracket_match = re.search(r'\[([A-Z_]+)\]', line)
        if bracket_match:
            return bracket_match.group(1).lower()

        # Infer from title
        title_lower = title.lower()
        type_mapping = {
            "definition": "definitions",
            "confidential": "confidentiality",
            "obligation": "obligations",
            "exclusion": "exclusions",
            "term": "term_and_termination",
            "terminat": "term_and_termination",
            "return": "return_of_materials",
            "remed": "remedies",
            "govern": "governing_law",
            "dispute": "dispute_resolution",
            "general": "general_provisions",
            "indemni": "indemnification",
            "liabilit": "limitation_of_liability",
            "intellectual": "intellectual_property",
            "data": "data_protection",
            "force": "force_majeure",
            "payment": "payment_terms",
            "scope": "scope_of_services",
            "warrant": "representations_warranties",
            "insurance": "insurance",
            "assign": "assignment",
            "notice": "notices",
            "sever": "severability",
        }

        for keyword, clause_type in type_mapping.items():
            if keyword in title_lower:
                return clause_type

        return "general"

    def _validate_contract(
        self,
        content: str,
        request: ContractGenerationRequest,
    ) -> Dict[str, Any]:
        """Validate the generated contract for basic legal requirements."""
        issues = []
        warnings = []

        # Check for placeholder text
        import re
        placeholders = re.findall(r'\[([A-Z_]+)\]', content)
        unfilled = [p for p in placeholders if not p.startswith(("ARTICLE", "SECTION"))]
        if unfilled:
            warnings.append(f"Found {len(unfilled)} unfilled placeholders: {unfilled[:5]}")

        # Check for essential clauses
        essential_clauses = ["governing law", "termination", "confidential"]
        content_lower = content.lower()
        for clause in essential_clauses:
            if clause not in content_lower:
                issues.append(f"Missing essential clause: {clause}")

        # Check minimum length
        if len(content) < 1000:
            warnings.append("Contract content is unusually short")

        # Check for signature block
        if "witness" not in content_lower and "signature" not in content_lower and "sign" not in content_lower:
            warnings.append("Missing signature block")

        # Calculate confidence
        confidence = 1.0
        confidence -= len(issues) * 0.1
        confidence -= len(warnings) * 0.02
        confidence = max(0.5, min(1.0, confidence))

        return {
            "valid": len(issues) == 0,
            "confidence": round(confidence, 2),
            "issues": issues,
            "warnings": warnings,
            "checks_performed": [
                "placeholder_check",
                "essential_clauses_check",
                "length_check",
                "signature_block_check",
            ],
        }

    def _get_party_prefix(self, contract_type: str, index: int) -> str:
        """Get the variable prefix for a party based on contract type."""
        prefixes = {
            "nda": ["disclosing_party", "receiving_party"],
            "msa": ["client", "provider"],
            "employment": ["employer", "employee"],
            "service_agreement": ["client", "provider"],
            "license": ["licensor", "licensee"],
            "partnership": ["partner_1", "partner_2"],
            "merger_acquisition": ["buyer", "seller"],
            "lease": ["landlord", "tenant"],
        }
        type_prefixes = prefixes.get(contract_type, ["party_a", "party_b"])
        return type_prefixes[min(index, len(type_prefixes) - 1)]

    def _generate_title(self, request: ContractGenerationRequest) -> str:
        """Generate a descriptive title for the contract."""
        type_names = {
            "nda": "Non-Disclosure Agreement",
            "msa": "Master Service Agreement",
            "employment": "Employment Agreement",
            "service_agreement": "Service Agreement",
            "license": "License Agreement",
            "partnership": "Partnership Agreement",
            "merger_acquisition": "Merger & Acquisition Agreement",
            "lease": "Commercial Lease Agreement",
            "consulting": "Consulting Agreement",
            "purchase_order": "Purchase Order",
            "loan": "Loan Agreement",
            "supply": "Supply Agreement",
            "distribution": "Distribution Agreement",
            "franchise": "Franchise Agreement",
            "joint_venture": "Joint Venture Agreement",
            "settlement": "Settlement Agreement",
            "custom": "Custom Agreement",
        }

        contract_name = type_names.get(request.contract_type, request.contract_type.replace("_", " ").title())
        party_names = " and ".join([p.name for p in request.parties[:2]])

        return f"{contract_name} - {party_names}"


# Singleton instance
contract_generator = ContractGenerator()
