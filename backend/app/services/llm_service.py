"""LLM Service - Multi-provider AI integration for legal contract operations."""

import json
import re
import time
from typing import Optional, Dict, Any, List, AsyncGenerator
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.exceptions import LLMServiceError, LLMRateLimitError

logger = structlog.get_logger(__name__)


# ─── Legal Domain Prompts ────────────────────────────────────────────────

LEGAL_SYSTEM_PROMPT = """You are an expert legal AI assistant specializing in contract law. 
You have deep knowledge across multiple legal systems including common law, civil law, and hybrid systems.
You are trained on millions of legal documents, court decisions, and regulatory requirements.

Key principles:
1. ACCURACY: Every legal statement must be precise and defensible
2. COMPLETENESS: Include all necessary legal provisions and protections
3. JURISDICTION: Respect jurisdictional requirements and local legal nuances
4. CLARITY: Use clear, unambiguous legal language
5. BALANCE: Draft fair provisions unless specifically instructed otherwise
6. COMPLIANCE: Ensure compliance with applicable regulations (GDPR, HIPAA, SOX, etc.)
7. PRECEDENT: Reference relevant legal precedents when applicable

You must NEVER:
- Generate legally invalid clauses
- Omit mandatory provisions for the jurisdiction
- Include provisions that violate public policy
- Use ambiguous language that could lead to disputes
- Ignore applicable regulatory requirements"""


CONTRACT_GENERATION_PROMPT = """Generate a comprehensive {contract_type} contract with the following specifications:

**Parties:**
{parties}

**Jurisdiction:** {jurisdiction}
**Governing Law:** {governing_law}
**Language:** {language}

**Key Terms:**
{key_terms}

**Special Requirements:**
{special_requirements}

**Industry:** {industry}

Generate a complete, legally-binding contract that includes:
1. All standard clauses required for this contract type
2. Jurisdiction-specific mandatory provisions
3. Industry-appropriate terms and conditions
4. Risk-mitigating provisions
5. Clear definitions section
6. Appropriate dispute resolution mechanism
7. Compliance with applicable regulations

Format the contract with proper legal numbering, clear section headers, and professional legal language.
The contract MUST be specific to the contract type requested — do NOT generate a generic NDA unless specifically asked.
Use the actual party names and details provided above throughout the contract.
Mark each clause with its type in brackets for analysis purposes."""


RISK_ANALYSIS_PROMPT = """Analyze the following contract for legal risks. Provide a comprehensive risk assessment.

**Contract Content:**
{contract_content}

**Contract Type:** {contract_type}
**Jurisdiction:** {jurisdiction}

Analyze the following risk categories:
1. Financial Risk - Payment terms, penalties, indemnification exposure
2. Regulatory Risk - Compliance with applicable laws and regulations
3. Operational Risk - Performance obligations, service levels, dependencies
4. Legal Liability - Liability caps, warranty provisions, representations
5. IP Risk - Intellectual property ownership, licensing, protection
6. Data Privacy - Personal data handling, breach notification, consent
7. Termination Risk - Exit provisions, post-termination obligations
8. Force Majeure - Coverage adequacy, notification requirements
9. Dispute Resolution - Mechanism adequacy, venue, governing law
10. Confidentiality - Scope, duration, exceptions

For EACH risk factor found, provide:
- Risk score (0.0-1.0)
- Category
- Specific clause reference
- Detailed explanation
- Recommended mitigation
- Relevant legal precedent (if applicable)
- Market standard comparison

Return the analysis as a structured JSON object."""


COMPLIANCE_CHECK_PROMPT = """Check the following contract for compliance with {jurisdiction} jurisdiction requirements 
and {regulations} regulations.

**Contract Content:**
{contract_content}

**Contract Type:** {contract_type}

For each applicable regulation, verify:
1. Mandatory clause inclusion
2. Prohibited clause detection
3. Language requirements
4. Filing/notification requirements
5. Consumer/worker protection provisions
6. Data protection compliance
7. Industry-specific requirements

For each check, provide:
- Rule reference
- Status (compliant/non-compliant/warning)
- Explanation
- Required remediation (if non-compliant)
- Severity level

Return as structured JSON."""


CLAUSE_EXPLANATION_PROMPT = """Explain the following legal clause in detail:

**Clause:**
{clause_content}

**Context:** Part of a {contract_type} contract under {jurisdiction} law.

Provide:
1. **Plain Language Explanation**: What this clause means in simple terms
2. **Legal Implications**: Rights and obligations created
3. **Risk Assessment**: Potential risks for each party
4. **Market Standard**: How this compares to typical provisions
5. **Relevant Precedents**: Key cases interpreting similar provisions
6. **Suggestions**: Potential improvements or alternatives
7. **Compliance Notes**: Any regulatory considerations

Be specific, cite relevant law where possible."""


# ─── LLM Provider Abstraction ───────────────────────────────────────────

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        response_format: Optional[str] = None,
    ) -> str:
        """Generate text completion."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming text completion."""
        pass

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get text embeddings for semantic search."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider implementation."""

    def __init__(self):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.DEFAULT_LLM_MODEL
        except Exception as e:
            logger.warning("OpenAI client initialization failed", error=str(e))
            self.client = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def generate(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        response_format: Optional[str] = None,
    ) -> str:
        if not self.client:
            raise LLMServiceError("OpenAI client not initialized", "openai")

        try:
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower():
                raise LLMRateLimitError("openai")
            raise LLMServiceError(f"OpenAI generation failed: {error_msg}", "openai")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            raise LLMServiceError("OpenAI client not initialized", "openai")

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise LLMServiceError(f"OpenAI streaming failed: {str(e)}", "openai")

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.client:
            raise LLMServiceError("OpenAI client not initialized", "openai")

        try:
            response = await self.client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise LLMServiceError(f"Embedding generation failed: {str(e)}", "openai")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation."""

    def __init__(self):
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = "claude-sonnet-4-20250514"
        except Exception as e:
            logger.warning("Anthropic client initialization failed", error=str(e))
            self.client = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def generate(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        response_format: Optional[str] = None,
    ) -> str:
        if not self.client:
            raise LLMServiceError("Anthropic client not initialized", "anthropic")

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            return response.content[0].text

        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower():
                raise LLMRateLimitError("anthropic")
            raise LLMServiceError(f"Anthropic generation failed: {error_msg}", "anthropic")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            raise LLMServiceError("Anthropic client not initialized", "anthropic")

        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            raise LLMServiceError(f"Anthropic streaming failed: {str(e)}", "anthropic")

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Anthropic doesn't have an embeddings API; fall back to sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            raise LLMServiceError(f"Embedding generation failed: {str(e)}", "anthropic")


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation using the new google.genai SDK."""

    def __init__(self):
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
            self.model_name = settings.DEFAULT_LLM_MODEL or "gemini-2.0-flash"
            self.client = genai.Client(api_key=settings.GOOGLE_GEMINI_API_KEY)
            logger.info("Gemini provider initialized", model=self.model_name)
        except Exception as e:
            logger.warning("Gemini client initialization failed", error=str(e))
            self.client = None
            self.genai = None
            self.types = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def generate(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        response_format: Optional[str] = None,
    ) -> str:
        if not self.client:
            raise LLMServiceError("Gemini client not initialized", "gemini")

        try:
            config_kwargs = {
                "system_instruction": system_prompt,
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            if response_format == "json":
                config_kwargs["response_mime_type"] = "application/json"

            config = self.types.GenerateContentConfig(**config_kwargs)

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )

            return response.text

        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise LLMRateLimitError("gemini")
            raise LLMServiceError(f"Gemini generation failed: {error_msg}", "gemini")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            raise LLMServiceError("Gemini client not initialized", "gemini")

        try:
            config = self.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            async for chunk in self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=config,
            ):
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            raise LLMServiceError(f"Gemini streaming failed: {str(e)}", "gemini")

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not self.client:
            raise LLMServiceError("Gemini client not initialized", "gemini")

        try:
            results = []
            for text in texts:
                response = await self.client.aio.models.embed_content(
                    model="text-embedding-004",
                    contents=text,
                )
                results.append(response.embeddings[0].values)
            return results
        except Exception as e:
            raise LLMServiceError(f"Gemini embedding failed: {str(e)}", "gemini")


class GroqProvider(LLMProvider):
    """Groq provider implementation using the Groq SDK (OpenAI-compatible)."""

    def __init__(self):
        try:
            from groq import AsyncGroq
            self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            self.model = settings.DEFAULT_LLM_MODEL or "llama-3.3-70b-versatile"
            logger.info("Groq provider initialized", model=self.model)
        except Exception as e:
            logger.warning("Groq client initialization failed", error=str(e))
            self.client = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def generate(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        response_format: Optional[str] = None,
    ) -> str:
        if not self.client:
            raise LLMServiceError("Groq client not initialized", "groq")

        try:
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower():
                raise LLMRateLimitError("groq")
            raise LLMServiceError(f"Groq generation failed: {error_msg}", "groq")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            raise LLMServiceError("Groq client not initialized", "groq")

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise LLMServiceError(f"Groq streaming failed: {str(e)}", "groq")

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Groq doesn't have an embeddings API; fall back to sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            embeddings = model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception:
            # Fallback to random embeddings if sentence-transformers not available
            import random
            return [[random.random() for _ in range(384)] for _ in texts]


class MockLLMProvider(LLMProvider):
    """Mock provider that generates prompt-aware contracts using the template engine.
    
    This provider parses the user's prompt to extract contract parameters and uses
    the TemplateEngine to generate a real, customized contract — NOT a hardcoded response.
    """

    async def generate(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        response_format: Optional[str] = None,
    ) -> str:
        if response_format == "json":
            return json.dumps(self._generate_mock_json(prompt))
        return self._generate_mock_contract(prompt)

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ) -> AsyncGenerator[str, None]:
        content = self._generate_mock_contract(prompt)
        words = content.split()
        for word in words:
            yield word + " "

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        import random
        return [[random.random() for _ in range(384)] for _ in texts]

    def _parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """Parse the generation prompt to extract contract parameters."""
        result = {
            "contract_type": "nda",
            "parties": [],
            "jurisdiction": "US-Federal",
            "governing_law": "US-Federal",
            "key_terms": {},
            "special_requirements": "",
            "industry": "general",
        }

        # Extract contract type
        type_match = re.search(
            r'(?:comprehensive|generate)\s+(\w[\w\s&/]+?)\s+contract',
            prompt, re.IGNORECASE
        )
        if type_match:
            raw_type = type_match.group(1).strip().lower()
            type_mapping = {
                "non-disclosure": "nda", "nda": "nda",
                "master service": "msa", "msa": "msa",
                "employment": "employment",
                "service": "service_agreement", "service agreement": "service_agreement",
                "license": "license", "software license": "license",
                "partnership": "partnership",
                "merger": "merger_acquisition", "merger & acquisition": "merger_acquisition",
                "merger_acquisition": "merger_acquisition",
                "lease": "lease", "commercial lease": "lease",
                "consulting": "consulting",
                "purchase order": "purchase_order", "purchase_order": "purchase_order",
                "loan": "loan",
                "supply": "supply",
                "distribution": "distribution",
                "franchise": "franchise",
                "joint venture": "joint_venture", "joint_venture": "joint_venture",
                "settlement": "settlement",
                "real estate": "real_estate", "real_estate": "real_estate",
            }
            for key, val in type_mapping.items():
                if key in raw_type:
                    result["contract_type"] = val
                    break

        # Extract parties
        party_lines = re.findall(
            r'-\s*([\w\s]+?):\s*([\w\s.,]+?)(?:\(|$)',
            prompt, re.MULTILINE
        )
        for role, name in party_lines:
            result["parties"].append({
                "name": name.strip().rstrip('.'),
                "role": role.strip(),
                "type": "corporation",
            })
        if not result["parties"]:
            result["parties"] = [
                {"name": "Party A", "role": "First Party", "type": "corporation"},
                {"name": "Party B", "role": "Second Party", "type": "corporation"},
            ]

        # Extract jurisdiction
        juris_match = re.search(r'\*\*Jurisdiction:\*\*\s*(.+)', prompt)
        if juris_match:
            result["jurisdiction"] = juris_match.group(1).strip()

        # Extract governing law
        gov_match = re.search(r'\*\*Governing Law:\*\*\s*(.+)', prompt)
        if gov_match:
            result["governing_law"] = gov_match.group(1).strip()

        # Extract industry
        ind_match = re.search(r'\*\*Industry:\*\*\s*(.+)', prompt)
        if ind_match:
            result["industry"] = ind_match.group(1).strip()

        # Extract special requirements
        req_match = re.search(r'\*\*Special Requirements:\*\*\s*(.+?)(?:\n\*\*|\Z)', prompt, re.DOTALL)
        if req_match:
            result["special_requirements"] = req_match.group(1).strip()

        # Extract key terms
        terms_section = re.search(r'\*\*Key Terms:\*\*\s*\n((?:-.+\n?)+)', prompt)
        if terms_section:
            for line in terms_section.group(1).strip().split('\n'):
                kv = line.strip().lstrip('- ').split(':', 1)
                if len(kv) == 2:
                    result["key_terms"][kv[0].strip()] = kv[1].strip()

        return result

    def _generate_mock_contract(self, prompt: str) -> str:
        """Generate a prompt-aware contract using the template engine."""
        from app.services.template_engine import TemplateEngine

        params = self._parse_prompt(prompt)
        contract_type = params["contract_type"]
        parties = params["parties"]
        jurisdiction = params["jurisdiction"]
        governing_law = params["governing_law"]
        key_terms = params["key_terms"]
        special_requirements = params["special_requirements"]

        engine = TemplateEngine()

        # Build variables for template rendering
        variables = {**key_terms}
        variables["governing_law_state"] = governing_law or jurisdiction
        variables["effective_date"] = key_terms.get(
            "effective_date",
            datetime.now(timezone.utc).strftime("%B %d, %Y"),
        )

        # Map parties to template variables using the engine's party prefix logic
        party_prefixes_map = {
            "nda": ["disclosing_party", "receiving_party"],
            "msa": ["client", "provider"],
            "employment": ["employer", "employee"],
            "service_agreement": ["client", "provider"],
            "license": ["licensor", "licensee"],
            "partnership": ["partner_1", "partner_2"],
            "merger_acquisition": ["buyer", "seller"],
            "lease": ["landlord", "tenant"],
            "consulting": ["client", "consultant"],
            "purchase_order": ["buyer", "seller"],
            "loan": ["lender", "borrower"],
            "supply": ["supplier", "buyer"],
            "distribution": ["distributor", "manufacturer"],
            "franchise": ["franchisor", "franchisee"],
            "joint_venture": ["partner_1", "partner_2"],
            "settlement": ["party_1", "party_2"],
        }
        prefixes = party_prefixes_map.get(contract_type, ["party_a", "party_b"])

        for i, party in enumerate(parties):
            prefix = prefixes[min(i, len(prefixes) - 1)]
            variables[f"{prefix}_name"] = party.get("name", f"[PARTY {i+1}]")
            variables[f"{prefix}_type"] = party.get("type", "corporation")
            variables[f"{prefix}_address"] = party.get("address", "[ADDRESS]")

        # Additional common variables
        variables.setdefault("term_years", key_terms.get("term_years", "2"))
        variables.setdefault("dispute_mechanism", key_terms.get("dispute_mechanism", "arbitration"))
        variables.setdefault("ip_ownership", key_terms.get("ip_ownership", "shared"))
        variables.setdefault("include_ip_indemnity", False)

        # Try to use the template engine first
        if contract_type in engine.templates:
            try:
                content = engine.build_contract_from_template(contract_type, variables)
                # Append special requirements if provided
                if special_requirements and special_requirements != "None specified":
                    content += f"\n\nSCHEDULE A: SPECIAL REQUIREMENTS\n\n{special_requirements}\n"
                return content
            except Exception as e:
                logger.warning(f"Template generation failed, using fallback: {e}")

        # Fallback: generate a basic contract structure for types without templates
        return self._generate_fallback_contract(
            contract_type, parties, jurisdiction, governing_law,
            key_terms, special_requirements
        )

    def _generate_fallback_contract(
        self,
        contract_type: str,
        parties: List[Dict],
        jurisdiction: str,
        governing_law: str,
        key_terms: Dict,
        special_requirements: str,
    ) -> str:
        """Generate a basic contract for types without dedicated templates."""
        type_names = {
            "nda": "NON-DISCLOSURE AGREEMENT",
            "msa": "MASTER SERVICE AGREEMENT",
            "employment": "EMPLOYMENT AGREEMENT",
            "service_agreement": "SERVICE AGREEMENT",
            "license": "SOFTWARE LICENSE AGREEMENT",
            "partnership": "PARTNERSHIP AGREEMENT",
            "merger_acquisition": "MERGER & ACQUISITION AGREEMENT",
            "lease": "COMMERCIAL LEASE AGREEMENT",
            "consulting": "CONSULTING AGREEMENT",
            "purchase_order": "PURCHASE ORDER AGREEMENT",
            "loan": "LOAN AGREEMENT",
            "supply": "SUPPLY AGREEMENT",
            "distribution": "DISTRIBUTION AGREEMENT",
            "franchise": "FRANCHISE AGREEMENT",
            "joint_venture": "JOINT VENTURE AGREEMENT",
            "settlement": "SETTLEMENT AGREEMENT",
            "real_estate": "REAL ESTATE AGREEMENT",
            "custom": "CUSTOM AGREEMENT",
        }

        title = type_names.get(contract_type, contract_type.replace("_", " ").upper() + " AGREEMENT")
        now = datetime.now(timezone.utc).strftime("%B %d, %Y")
        effective_date = key_terms.get("effective_date", now)

        # Build parties block
        parties_block = ""
        for i, party in enumerate(parties):
            name = party.get("name", f"Party {chr(65 + i)}")
            role = party.get("role", f"Party {chr(65 + i)}")
            entity_type = party.get("type", "corporation")
            address = party.get("address", "[ADDRESS]")
            parties_block += f"""
{name}, a {entity_type} with its principal place of business at 
{address} ("{role}");
"""

        # Build key terms block
        terms_block = ""
        if key_terms:
            terms_block = "\nARTICLE 2. KEY TERMS\n\n"
            for i, (k, v) in enumerate(key_terms.items(), 1):
                terms_block += f'2.{i} "{k.replace("_", " ").title()}" means {v}.\n\n'

        # Build special requirements block
        special_block = ""
        if special_requirements and special_requirements != "None specified":
            special_block = f"""
ARTICLE 10. SPECIAL PROVISIONS

{special_requirements}
"""

        term_years = key_terms.get("term_years", "1")

        contract = f"""{'=' * 80}
{title}
{'=' * 80}

THIS {title} (this "Agreement") is entered into as of 
{effective_date} (the "Effective Date"),

BETWEEN:
{parties_block}
(each a "Party" and collectively the "Parties").

RECITALS

WHEREAS, the Parties desire to enter into this {title.lower()} to establish the 
terms and conditions governing their business relationship; and

WHEREAS, the Parties acknowledge that this Agreement shall be governed by the laws 
of {governing_law};

NOW, THEREFORE, in consideration of the mutual covenants and agreements herein 
contained, and for other good and valuable consideration, the receipt and sufficiency 
of which are hereby acknowledged, the Parties agree as follows:

ARTICLE 1. DEFINITIONS

1.1 "Agreement" means this {title} and all exhibits, schedules, and amendments 
attached hereto or incorporated by reference.

1.2 "Affiliate" means any entity that directly or indirectly controls, is controlled 
by, or is under common control with a Party, where "control" means ownership of more 
than fifty percent (50%) of the voting securities.

1.3 "Business Day" means any day other than a Saturday, Sunday, or public holiday 
in {jurisdiction}.

1.4 "Confidential Information" means any information designated as confidential or 
that reasonably should be understood to be confidential given the nature of the 
information and circumstances of disclosure.
{terms_block}
ARTICLE 3. SCOPE AND PURPOSE

3.1 This Agreement sets forth the terms and conditions under which the Parties 
shall conduct their business relationship as described herein.

3.2 Each Party shall perform its obligations under this Agreement in good faith 
and in accordance with applicable law.

ARTICLE 4. REPRESENTATIONS AND WARRANTIES

4.1 Each Party represents and warrants that:

(a) it has full power and authority to enter into and perform this Agreement;
(b) the execution and performance of this Agreement does not conflict with any 
    other agreement to which it is a party;
(c) it shall comply with all applicable laws and regulations in performing its 
    obligations hereunder.

ARTICLE 5. CONFIDENTIALITY

5.1 Each Party receiving Confidential Information shall:

(a) hold such Confidential Information in strict confidence;
(b) not disclose such Confidential Information to any third party without prior 
    written consent;
(c) use such Confidential Information solely for the purposes of this Agreement;
(d) protect such Confidential Information using the same degree of care it uses 
    to protect its own confidential information.

5.2 The obligations of confidentiality shall survive for a period of five (5) 
years following the termination of this Agreement.

ARTICLE 6. TERM AND TERMINATION

6.1 This Agreement shall commence on the Effective Date and continue for a period 
of {term_years} year(s) unless earlier terminated as provided herein.

6.2 Either Party may terminate this Agreement upon thirty (30) days' prior written 
notice to the other Party.

6.3 Either Party may terminate this Agreement immediately upon written notice if 
the other Party materially breaches this Agreement and fails to cure such breach 
within thirty (30) days after receiving written notice.

ARTICLE 7. LIMITATION OF LIABILITY

7.1 IN NO EVENT SHALL EITHER PARTY BE LIABLE TO THE OTHER PARTY FOR ANY INDIRECT, 
INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES.

7.2 EACH PARTY'S TOTAL AGGREGATE LIABILITY SHALL NOT EXCEED THE TOTAL FEES PAID 
OR PAYABLE UNDER THIS AGREEMENT DURING THE TWELVE (12) MONTHS PRECEDING THE CLAIM.

ARTICLE 8. INDEMNIFICATION

8.1 Each Party shall indemnify, defend, and hold harmless the other Party from 
and against any and all claims, damages, losses, liabilities, costs, and expenses 
arising out of or related to:

(a) the indemnifying Party's material breach of this Agreement;
(b) the indemnifying Party's negligence or willful misconduct;
(c) any violation of applicable law by the indemnifying Party.

ARTICLE 9. GOVERNING LAW AND DISPUTE RESOLUTION

9.1 This Agreement shall be governed by and construed in accordance with the laws 
of {governing_law}, without giving effect to any choice or conflict of law 
provision or rule.

9.2 Any dispute arising out of or relating to this Agreement shall be resolved 
through binding arbitration administered by the American Arbitration Association 
under its Commercial Arbitration Rules.

9.3 The prevailing Party in any action to enforce this Agreement shall be entitled 
to recover reasonable attorneys' fees and costs.
{special_block}
ARTICLE 11. GENERAL PROVISIONS

11.1 Entire Agreement. This Agreement constitutes the entire agreement between 
the Parties with respect to the subject matter hereof.

11.2 Amendment. No amendment shall be effective unless in writing and signed by 
both Parties.

11.3 Waiver. No waiver of any provision shall constitute a waiver of any other 
provision or a continuing waiver.

11.4 Severability. If any provision is found to be invalid or unenforceable, the 
remaining provisions shall continue in full force and effect.

11.5 Assignment. Neither Party may assign this Agreement without the prior written 
consent of the other Party.

11.6 Notices. All notices shall be in writing and delivered by certified mail, 
overnight courier, or email to the addresses specified herein.

11.7 Counterparts. This Agreement may be executed in counterparts, each of which 
shall be deemed an original.

11.8 Force Majeure. Neither Party shall be liable for any failure or delay in 
performing its obligations due to circumstances beyond its reasonable control.

IN WITNESS WHEREOF, the Parties have executed this Agreement as of the Effective Date.

"""
        for party in parties:
            name = party.get("name", "[PARTY NAME]")
            contract += f"""{name}

By: ________________________________
Name: ______________________________
Title: _____________________________
Date: ______________________________

"""

        return contract

    def _generate_mock_json(self, prompt: str) -> dict:
        """Generate prompt-aware mock JSON response for analysis prompts."""
        params = self._parse_prompt(prompt)

        if "risk" in prompt.lower():
            return {
                "overall_risk_score": 0.35,
                "risk_level": "medium",
                "confidence": 0.92,
                "contract_type_analyzed": params.get("contract_type", "unknown"),
                "jurisdiction_analyzed": params.get("jurisdiction", "unknown"),
                "risk_factors": [
                    {
                        "category": "financial",
                        "factor": "Liability exposure may be uncapped in certain scenarios",
                        "score": 0.6,
                        "clause_reference": "Article 7 - Limitation of Liability",
                        "explanation": "The liability cap refers to fees paid, which may be insufficient for high-value disputes",
                        "remediation": "Consider adding a fixed monetary cap on total liability",
                        "precedent": f"Standard commercial practice in {params.get('jurisdiction', 'US-Federal')}"
                    },
                    {
                        "category": "confidentiality",
                        "factor": "Broad definition of confidential information",
                        "score": 0.3,
                        "clause_reference": "Article 5 - Confidentiality",
                        "explanation": "Definition may inadvertently capture publicly available information",
                        "remediation": "Add explicit carve-outs for publicly known information",
                        "precedent": "Tech Solutions v. Data Corp (2022)"
                    },
                    {
                        "category": "termination",
                        "factor": "Short notice period for termination",
                        "score": 0.4,
                        "clause_reference": "Article 6 - Term and Termination",
                        "explanation": "30-day notice may be insufficient for complex arrangements",
                        "remediation": "Consider 60-90 day notice period for material contracts",
                        "precedent": "Standard industry practice"
                    },
                    {
                        "category": "dispute_resolution",
                        "factor": "Arbitration venue not specified",
                        "score": 0.5,
                        "clause_reference": "Article 9 - Dispute Resolution",
                        "explanation": "Lack of specified venue could lead to jurisdictional disputes",
                        "remediation": f"Specify arbitration venue within {params.get('jurisdiction', 'the governing jurisdiction')}",
                        "precedent": "Per AAA Commercial Arbitration Rules"
                    },
                ],
                "key_findings": [
                    "Liability cap is relative to fees paid — may be insufficient",
                    "No specific data protection clause for GDPR/CCPA compliance",
                    "Arbitration clause lacks specificity on venue and language",
                    "Force majeure clause is basic — consider expanding scope",
                ],
                "recommendations": [
                    "Add monetary cap on damages",
                    "Include data protection addendum if handling personal data",
                    "Specify arbitration venue, language, and rules version",
                    "Add insurance requirements for high-value contracts",
                ],
            }
        elif "compliance" in prompt.lower():
            return {
                "overall_status": "partial",
                "compliance_score": 0.78,
                "jurisdiction_checked": params.get("jurisdiction", "unknown"),
                "contract_type_checked": params.get("contract_type", "unknown"),
                "checks": [
                    {
                        "rule": "Data Protection Requirements",
                        "status": "warning",
                        "explanation": "Contract may need explicit data processing terms if personal data is involved",
                        "remediation": "Add Data Processing Agreement annex if applicable",
                        "severity": "high"
                    },
                    {
                        "rule": "Statute of Frauds",
                        "status": "compliant",
                        "explanation": "Agreement is in writing and includes signature blocks",
                        "severity": "low"
                    },
                    {
                        "rule": "Governing Law Clause",
                        "status": "compliant",
                        "explanation": f"Governing law ({params.get('governing_law', 'specified')}) is clearly stated",
                        "severity": "low"
                    },
                    {
                        "rule": "Termination Notice Requirements",
                        "status": "compliant",
                        "explanation": "Notice period and method are specified",
                        "severity": "medium"
                    },
                ],
                "required_actions": [
                    "Review data protection requirements for the applicable jurisdiction",
                    "Verify enforceability of dispute resolution mechanism in target jurisdiction",
                ],
            }
        else:
            return {"status": "success", "message": "Analysis complete"}


# ─── LLM Service Factory ────────────────────────────────────────────────

class LLMService:
    """Factory and manager for LLM providers."""

    _providers: Dict[str, LLMProvider] = {}
    _active_provider_name: str = "mock"

    def __init__(self):
        self._providers = {}  # Instance-level dict to avoid class-level sharing
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available LLM providers."""
        # Always register mock provider for fallback
        self._providers["mock"] = MockLLMProvider()

        if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your-groq-api-key-here":
            try:
                self._providers["groq"] = GroqProvider()
                self._active_provider_name = "groq"
                logger.info("Groq provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq provider: {e}")

        if settings.GOOGLE_GEMINI_API_KEY and settings.GOOGLE_GEMINI_API_KEY != "your-gemini-api-key-here":
            try:
                self._providers["gemini"] = GeminiProvider()
                if self._active_provider_name == "mock":
                    self._active_provider_name = "gemini"
                logger.info("Gemini provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini provider: {e}")

        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key-here":
            try:
                self._providers["openai"] = OpenAIProvider()
                if self._active_provider_name == "mock":
                    self._active_provider_name = "openai"
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")

        if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != "your-anthropic-api-key-here":
            try:
                self._providers["anthropic"] = AnthropicProvider()
                if self._active_provider_name == "mock":
                    self._active_provider_name = "anthropic"
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic provider: {e}")

        if len(self._providers) == 1:  # Only mock
            logger.warning(
                "No LLM API keys configured — using mock provider. "
                "Contracts will be generated from templates. "
                "Set GROQ_API_KEY, GOOGLE_GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY for AI-powered generation."
            )

    def get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        """Get an LLM provider by name or default."""
        name = provider_name or settings.DEFAULT_LLM_PROVIDER

        if name in self._providers:
            return self._providers[name]

        # Fallback chain: groq -> gemini -> openai -> anthropic -> mock
        for fallback in ["groq", "gemini", "openai", "anthropic", "mock"]:
            if fallback in self._providers:
                logger.info(f"Falling back to {fallback} provider")
                return self._providers[fallback]

        return self._providers["mock"]

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all LLM providers."""
        return {
            "active_provider": self._active_provider_name,
            "available_providers": list(self._providers.keys()),
            "is_ai_powered": self._active_provider_name != "mock",
            "configured_default": settings.DEFAULT_LLM_PROVIDER,
        }

    async def generate_contract(
        self,
        contract_type: str,
        parties: List[Dict[str, str]],
        jurisdiction: str,
        governing_law: str,
        key_terms: Dict[str, Any],
        special_requirements: str = "",
        industry: str = "general",
        language: str = "en",
        provider: Optional[str] = None,
    ) -> str:
        """Generate a contract using configured LLM."""
        start_time = time.time()

        parties_str = "\n".join(
            [f"- {p.get('role', 'Party')}: {p.get('name', 'N/A')} ({p.get('type', 'entity')})"
             for p in parties]
        )

        terms_str = "\n".join(
            [f"- {k}: {v}" for k, v in key_terms.items()]
        )

        prompt = CONTRACT_GENERATION_PROMPT.format(
            contract_type=contract_type,
            parties=parties_str,
            jurisdiction=jurisdiction,
            governing_law=governing_law,
            language=language,
            key_terms=terms_str,
            special_requirements=special_requirements or "None specified",
            industry=industry,
        )

        llm = self.get_provider(provider)
        result = await llm.generate(prompt, temperature=0.1, max_tokens=settings.LLM_MAX_TOKENS)

        duration = time.time() - start_time
        logger.info(
            "Contract generated",
            contract_type=contract_type,
            jurisdiction=jurisdiction,
            duration_s=round(duration, 2),
            provider=provider or self._active_provider_name,
        )

        return result

    async def analyze_risks(
        self,
        contract_content: str,
        contract_type: str,
        jurisdiction: str,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze contract risks using LLM."""
        prompt = RISK_ANALYSIS_PROMPT.format(
            contract_content=contract_content[:12000],  # Truncate for context limits
            contract_type=contract_type,
            jurisdiction=jurisdiction,
        )

        llm = self.get_provider(provider)
        result = await llm.generate(prompt, response_format="json", max_tokens=settings.LLM_MAX_TOKENS)

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("Failed to parse risk analysis JSON, returning raw")
            return {"raw_analysis": result, "parse_error": True}

    async def check_compliance(
        self,
        contract_content: str,
        contract_type: str,
        jurisdiction: str,
        regulations: List[str],
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check contract compliance using LLM."""
        prompt = COMPLIANCE_CHECK_PROMPT.format(
            contract_content=contract_content[:12000],
            contract_type=contract_type,
            jurisdiction=jurisdiction,
            regulations=", ".join(regulations),
        )

        llm = self.get_provider(provider)
        result = await llm.generate(prompt, response_format="json", max_tokens=settings.LLM_MAX_TOKENS)

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw_analysis": result, "parse_error": True}

    async def explain_clause(
        self,
        clause_content: str,
        contract_type: str,
        jurisdiction: str,
        provider: Optional[str] = None,
    ) -> str:
        """Get detailed explanation of a legal clause."""
        prompt = CLAUSE_EXPLANATION_PROMPT.format(
            clause_content=clause_content,
            contract_type=contract_type,
            jurisdiction=jurisdiction,
        )

        llm = self.get_provider(provider)
        return await llm.generate(prompt, max_tokens=2048)

    async def get_embeddings(
        self,
        texts: List[str],
        provider: Optional[str] = None,
    ) -> List[List[float]]:
        """Get text embeddings for semantic search."""
        llm = self.get_provider(provider)
        return await llm.get_embeddings(texts)


# Singleton instance
llm_service = LLMService()
