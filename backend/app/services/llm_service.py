"""LLM Service - Multi-provider AI integration for legal contract operations."""

import json
import time
from typing import Optional, Dict, Any, List, AsyncGenerator
from abc import ABC, abstractmethod

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
        max_tokens: int = 4096,
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
        max_tokens: int = 4096,
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
        max_tokens: int = 4096,
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
        max_tokens: int = 4096,
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
        max_tokens: int = 4096,
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
        max_tokens: int = 4096,
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


class MockLLMProvider(LLMProvider):
    """Mock provider for testing and development without API keys."""

    async def generate(
        self,
        prompt: str,
        system_prompt: str = LEGAL_SYSTEM_PROMPT,
        temperature: float = 0.1,
        max_tokens: int = 4096,
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
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        content = self._generate_mock_contract(prompt)
        words = content.split()
        for word in words:
            yield word + " "

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        import random
        return [[random.random() for _ in range(384)] for _ in texts]

    def _generate_mock_contract(self, prompt: str) -> str:
        """Generate a realistic mock contract for development."""
        return """
MUTUAL NON-DISCLOSURE AGREEMENT

THIS MUTUAL NON-DISCLOSURE AGREEMENT (this "Agreement") is entered into as of the date 
last signed below (the "Effective Date"), by and between:

Party A: [PARTY_A_NAME], a [PARTY_A_TYPE] organized under the laws of [PARTY_A_JURISDICTION], 
with its principal place of business at [PARTY_A_ADDRESS] ("Disclosing Party");

AND

Party B: [PARTY_B_NAME], a [PARTY_B_TYPE] organized under the laws of [PARTY_B_JURISDICTION], 
with its principal place of business at [PARTY_B_ADDRESS] ("Receiving Party");

(each a "Party" and collectively the "Parties").

RECITALS

WHEREAS, the Parties wish to explore a potential business relationship (the "Purpose"); and

WHEREAS, in connection with the Purpose, each Party may disclose to the other certain 
confidential and proprietary information;

NOW, THEREFORE, in consideration of the mutual covenants and agreements herein contained, 
and for other good and valuable consideration, the receipt and sufficiency of which are 
hereby acknowledged, the Parties agree as follows:

[CONFIDENTIALITY] 1. DEFINITIONS

1.1 "Confidential Information" means any and all non-public, proprietary, or confidential 
information disclosed by either Party to the other Party, whether orally, in writing, 
electronically, or by any other means, including but not limited to:

(a) trade secrets, inventions, ideas, processes, formulas, source code, object code, 
    data, programs, know-how, improvements, discoveries, developments, designs, and techniques;

(b) financial information, business plans, marketing strategies, customer lists, supplier 
    information, pricing data, and projections;

(c) technical specifications, engineering drawings, algorithms, and research data;

(d) any information that is marked or designated as "confidential," "proprietary," or with 
    similar designation; and

(e) any information that a reasonable person would understand to be confidential given the 
    nature of the information and circumstances of disclosure.

1.2 "Representative" means a Party's directors, officers, employees, agents, advisors, 
consultants, and contractors who need to know Confidential Information for the Purpose.

[OBLIGATIONS] 2. OBLIGATIONS OF RECEIVING PARTY

2.1 The Receiving Party shall:

(a) hold Confidential Information in strict confidence using the same degree of care it uses 
    to protect its own confidential information, but in no event less than reasonable care;

(b) not disclose Confidential Information to any third party without the prior written consent 
    of the Disclosing Party;

(c) use Confidential Information solely for the Purpose;

(d) limit disclosure of Confidential Information to its Representatives who have a need to 
    know and are bound by confidentiality obligations no less restrictive than this Agreement;

(e) immediately notify the Disclosing Party upon discovery of any unauthorized use or 
    disclosure of Confidential Information.

[EXCLUSIONS] 3. EXCLUSIONS

3.1 Confidential Information does not include information that:

(a) is or becomes publicly available through no fault of the Receiving Party;
(b) was known to the Receiving Party prior to disclosure, as evidenced by written records;
(c) is independently developed by the Receiving Party without use of Confidential Information;
(d) is rightfully obtained from a third party without restriction on disclosure.

[TERM] 4. TERM AND TERMINATION

4.1 This Agreement shall be effective from the Effective Date and shall continue for a period 
of two (2) years unless earlier terminated by either Party upon thirty (30) days' written notice.

4.2 The obligations of confidentiality shall survive termination of this Agreement for a 
period of five (5) years from the date of disclosure of the relevant Confidential Information.

[RETURN_OF_MATERIALS] 5. RETURN OF MATERIALS

5.1 Upon termination of this Agreement or upon request by the Disclosing Party, the Receiving 
Party shall promptly return or destroy all Confidential Information and certify such 
destruction in writing.

[REMEDIES] 6. REMEDIES

6.1 The Parties acknowledge that a breach of this Agreement may cause irreparable harm for 
which monetary damages would be inadequate. Accordingly, the Disclosing Party shall be 
entitled to seek equitable relief, including injunction and specific performance, in addition 
to all other remedies available at law or in equity.

[GOVERNING_LAW] 7. GOVERNING LAW AND DISPUTE RESOLUTION

7.1 This Agreement shall be governed by and construed in accordance with the laws of the 
State of [GOVERNING_LAW_STATE], without regard to its conflict of law principles.

7.2 Any dispute arising out of or relating to this Agreement shall be resolved through 
binding arbitration administered by the American Arbitration Association under its 
Commercial Arbitration Rules.

[GENERAL_PROVISIONS] 8. GENERAL PROVISIONS

8.1 Entire Agreement. This Agreement constitutes the entire agreement between the Parties 
with respect to the subject matter hereof and supersedes all prior negotiations, 
representations, warranties, commitments, offers, and agreements.

8.2 Amendment. No amendment to this Agreement shall be effective unless in writing and 
signed by both Parties.

8.3 Waiver. No waiver of any provision of this Agreement shall constitute a waiver of any 
other provision or a continuing waiver.

8.4 Severability. If any provision of this Agreement is found to be invalid or unenforceable, 
the remaining provisions shall continue in full force and effect.

8.5 Assignment. Neither Party may assign this Agreement without the prior written consent 
of the other Party.

8.6 Notices. All notices under this Agreement shall be in writing and delivered by certified 
mail, overnight courier, or email to the addresses specified above.

8.7 Counterparts. This Agreement may be executed in counterparts, each of which shall be 
deemed an original.

IN WITNESS WHEREOF, the Parties have executed this Agreement as of the Effective Date.

[PARTY_A_NAME]                          [PARTY_B_NAME]
By: ________________________            By: ________________________
Name: ______________________            Name: ______________________
Title: _____________________            Title: _____________________
Date: ______________________            Date: ______________________
"""

    def _generate_mock_json(self, prompt: str) -> dict:
        """Generate mock JSON response for analysis prompts."""
        if "risk" in prompt.lower():
            return {
                "overall_risk_score": 0.35,
                "risk_level": "medium",
                "confidence": 0.92,
                "risk_factors": [
                    {
                        "category": "financial",
                        "factor": "Unlimited liability exposure",
                        "score": 0.6,
                        "clause_reference": "Section 6.1",
                        "explanation": "No cap on liability for breaches",
                        "remediation": "Add liability cap provision",
                        "precedent": "ABC Corp v. XYZ Inc. (2023)"
                    },
                    {
                        "category": "confidentiality",
                        "factor": "Broad definition of confidential information",
                        "score": 0.3,
                        "clause_reference": "Section 1.1",
                        "explanation": "Definition may capture publicly available information",
                        "remediation": "Narrow the definition scope",
                        "precedent": "Tech Solutions v. Data Corp (2022)"
                    },
                    {
                        "category": "termination",
                        "factor": "Short notice period",
                        "score": 0.4,
                        "clause_reference": "Section 4.1",
                        "explanation": "30-day notice may be insufficient for complex arrangements",
                        "remediation": "Consider 60-90 day notice period",
                        "precedent": "Standard industry practice"
                    }
                ],
                "key_findings": [
                    "Missing limitation of liability clause",
                    "Non-compete provisions may be unenforceable in certain jurisdictions",
                    "Arbitration clause lacks specificity on venue"
                ],
                "recommendations": [
                    "Add monetary cap on damages",
                    "Include carve-outs for IP infringement",
                    "Specify arbitration venue and rules"
                ]
            }
        elif "compliance" in prompt.lower():
            return {
                "overall_status": "partial",
                "compliance_score": 0.78,
                "checks": [
                    {
                        "rule": "GDPR Art. 28 - Data Processing",
                        "status": "warning",
                        "explanation": "Contract lacks explicit data processing terms",
                        "remediation": "Add Data Processing Agreement annex",
                        "severity": "high"
                    },
                    {
                        "rule": "Statute of Frauds",
                        "status": "compliant",
                        "explanation": "Agreement is in writing and signed by parties",
                        "severity": "low"
                    },
                    {
                        "rule": "Non-Compete Duration",
                        "status": "compliant",
                        "explanation": "Confidentiality period is within reasonable bounds",
                        "severity": "medium"
                    }
                ],
                "required_actions": [
                    "Add GDPR data processing provisions if EU personal data is involved",
                    "Verify enforceability of non-compete in target jurisdictions"
                ]
            }
        else:
            return {"status": "success", "message": "Analysis complete"}


# ─── LLM Service Factory ────────────────────────────────────────────────

class LLMService:
    """Factory and manager for LLM providers."""

    _providers: Dict[str, LLMProvider] = {}

    def __init__(self):
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize available LLM providers."""
        # Always register mock provider for fallback
        self._providers["mock"] = MockLLMProvider()

        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key-here":
            self._providers["openai"] = OpenAIProvider()
            logger.info("OpenAI provider initialized")

        if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY != "your-anthropic-api-key-here":
            self._providers["anthropic"] = AnthropicProvider()
            logger.info("Anthropic provider initialized")

        if len(self._providers) == 1:  # Only mock
            logger.warning("No LLM API keys configured, using mock provider")

    def get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        """Get an LLM provider by name or default."""
        name = provider_name or settings.DEFAULT_LLM_PROVIDER

        if name in self._providers:
            return self._providers[name]

        # Fallback chain
        for fallback in ["openai", "anthropic", "mock"]:
            if fallback in self._providers:
                logger.info(f"Falling back to {fallback} provider")
                return self._providers[fallback]

        return self._providers["mock"]

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
            provider=provider or settings.DEFAULT_LLM_PROVIDER,
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
