"""Compliance Checking Service - Multi-jurisdictional regulatory compliance verification."""

import uuid
import time
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import structlog
from pydantic import BaseModel, Field

from app.config import settings
from app.core.exceptions import ComplianceViolationError, JurisdictionNotSupportedError
from app.services.llm_service import llm_service

logger = structlog.get_logger(__name__)


# ─── Compliance Rule Definitions ─────────────────────────────────────────

COMPLIANCE_RULES: List[Dict[str, Any]] = [
    # GDPR Rules
    {
        "code": "GDPR-001", "title": "Data Processing Agreement Required",
        "category": "GDPR", "severity": "critical",
        "jurisdictions": ["EU-GDPR", "EU-DE", "EU-FR", "EU-ES", "UK", "NL", "BE", "IT", "AT", "IE", "SE", "NO", "DK", "FI", "CH"],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["data processing", "processor", "controller", "personal data"],
        "description": "Contracts involving personal data must include a Data Processing Agreement per GDPR Article 28",
    },
    {
        "code": "GDPR-002", "title": "Data Subject Rights",
        "category": "GDPR", "severity": "high",
        "jurisdictions": ["EU-GDPR", "EU-DE", "EU-FR", "EU-ES", "UK"],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["data subject rights", "access", "rectification", "erasure", "right to be forgotten"],
        "description": "Must include provisions for data subject rights under GDPR Articles 15-22",
    },
    {
        "code": "GDPR-003", "title": "International Data Transfer Safeguards",
        "category": "GDPR", "severity": "critical",
        "jurisdictions": ["EU-GDPR", "EU-DE", "EU-FR", "EU-ES", "UK"],
        "rule_type": "conditional",
        "required_keywords": ["standard contractual clauses", "adequacy decision", "binding corporate rules", "data transfer"],
        "description": "Cross-border data transfers require appropriate safeguards per GDPR Chapter V",
    },
    {
        "code": "GDPR-004", "title": "Breach Notification Timeline",
        "category": "GDPR", "severity": "critical",
        "jurisdictions": ["EU-GDPR", "EU-DE", "EU-FR", "EU-ES", "UK"],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["72 hours", "breach notification", "without undue delay"],
        "description": "Data breach notification within 72 hours per GDPR Article 33",
    },

    # HIPAA Rules
    {
        "code": "HIPAA-001", "title": "Business Associate Agreement",
        "category": "HIPAA", "severity": "critical",
        "jurisdictions": ["US-Federal", "US-CA", "US-NY", "US-TX", "US-FL", "US-IL"],
        "contract_types": ["service_agreement", "msa", "consulting"],
        "rule_type": "conditional",
        "required_keywords": ["business associate", "protected health information", "phi", "hipaa"],
        "description": "Healthcare data handling requires BAA under HIPAA",
    },
    {
        "code": "HIPAA-002", "title": "PHI Safeguards",
        "category": "HIPAA", "severity": "critical",
        "jurisdictions": ["US-Federal"],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["administrative safeguards", "physical safeguards", "technical safeguards"],
        "description": "Must specify safeguards for Protected Health Information",
    },
    {
        "code": "HIPAA-003", "title": "PHI Use and Disclosure Limitations",
        "category": "HIPAA", "severity": "high",
        "jurisdictions": ["US-Federal"],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["minimum necessary", "permitted use", "permitted disclosure"],
        "description": "Must limit PHI use and disclosure to minimum necessary",
    },

    # SOX Rules
    {
        "code": "SOX-001", "title": "Internal Controls Documentation",
        "category": "SOX", "severity": "high",
        "jurisdictions": ["US-Federal"],
        "contract_types": ["msa", "service_agreement", "consulting"],
        "rule_type": "conditional",
        "required_keywords": ["internal controls", "audit", "financial reporting", "sox compliance"],
        "description": "Financial services contracts must address SOX internal controls",
    },
    {
        "code": "SOX-002", "title": "Audit Rights",
        "category": "SOX", "severity": "high",
        "jurisdictions": ["US-Federal"],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["audit rights", "right to audit", "inspection rights"],
        "description": "Must include audit rights for SOX compliance",
    },

    # CCPA/CPRA Rules
    {
        "code": "CCPA-001", "title": "Consumer Data Rights",
        "category": "CCPA", "severity": "high",
        "jurisdictions": ["US-CA"],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["consumer rights", "right to know", "right to delete", "right to opt-out", "do not sell"],
        "description": "California contracts must address CCPA/CPRA consumer data rights",
    },
    {
        "code": "CCPA-002", "title": "Service Provider Obligations",
        "category": "CCPA", "severity": "high",
        "jurisdictions": ["US-CA"],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["service provider", "business purpose", "personal information"],
        "description": "CCPA requirements for service provider data handling",
    },

    # Employment Law Rules
    {
        "code": "EMP-001", "title": "At-Will Employment Disclaimer",
        "category": "Employment", "severity": "high",
        "jurisdictions": ["US-Federal", "US-CA", "US-NY", "US-TX"],
        "contract_types": ["employment"],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["at-will", "at will employment"],
        "description": "US employment contracts should include at-will disclaimer where applicable",
    },
    {
        "code": "EMP-002", "title": "Non-Compete Enforceability",
        "category": "Employment", "severity": "critical",
        "jurisdictions": ["US-CA"],
        "contract_types": ["employment", "consulting"],
        "rule_type": "prohibited",
        "prohibited_keywords": ["non-compete", "non-competition", "covenant not to compete"],
        "description": "Non-compete clauses are generally void in California (Bus. & Prof. Code §16600)",
    },
    {
        "code": "EMP-003", "title": "Restrictive Covenant Reasonableness",
        "category": "Employment", "severity": "high",
        "jurisdictions": ["US-NY", "US-TX", "US-FL", "US-IL", "UK"],
        "contract_types": ["employment"],
        "rule_type": "conditional",
        "required_keywords": ["reasonable", "geographic scope", "time limitation"],
        "description": "Restrictive covenants must be reasonable in scope, geography, and duration",
    },

    # General Contract Law Rules
    {
        "code": "GEN-001", "title": "Governing Law Clause",
        "category": "General", "severity": "high",
        "jurisdictions": [],  # All jurisdictions
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["governing law", "governed by", "construed in accordance"],
        "description": "All contracts should specify governing law",
    },
    {
        "code": "GEN-002", "title": "Dispute Resolution Mechanism",
        "category": "General", "severity": "medium",
        "jurisdictions": [],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["dispute resolution", "arbitration", "mediation", "jurisdiction"],
        "description": "Contracts should include dispute resolution provisions",
    },
    {
        "code": "GEN-003", "title": "Severability Clause",
        "category": "General", "severity": "medium",
        "jurisdictions": [],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["severability", "severable", "invalid provision"],
        "description": "Including a severability clause protects the contract if any provision is invalidated",
    },
    {
        "code": "GEN-004", "title": "Entire Agreement Clause",
        "category": "General", "severity": "medium",
        "jurisdictions": [],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["entire agreement", "whole agreement", "complete agreement"],
        "description": "Integration/merger clause prevents reliance on prior representations",
    },
    {
        "code": "GEN-005", "title": "Force Majeure Provision",
        "category": "General", "severity": "medium",
        "jurisdictions": [],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["force majeure", "acts of god", "unforeseeable circumstances"],
        "description": "Force majeure clause addresses performance excuses for extraordinary events",
    },
    {
        "code": "GEN-006", "title": "Assignment Restrictions",
        "category": "General", "severity": "medium",
        "jurisdictions": [],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["assignment", "transfer", "without consent"],
        "description": "Assignment clause controls transferability of contract rights",
    },
    {
        "code": "GEN-007", "title": "Notice Provisions",
        "category": "General", "severity": "low",
        "jurisdictions": [],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["notice", "written notice", "notification"],
        "description": "Notice provisions specify how formal communications must be delivered",
    },

    # International Trade
    {
        "code": "INT-001", "title": "INCOTERMS Reference",
        "category": "International", "severity": "high",
        "jurisdictions": [],
        "contract_types": ["supply", "distribution", "purchase_order"],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["incoterms", "fob", "cif", "dap", "exw"],
        "description": "International trade contracts should reference INCOTERMS for delivery terms",
    },
    {
        "code": "INT-002", "title": "Currency and Payment Terms",
        "category": "International", "severity": "high",
        "jurisdictions": [],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["currency", "exchange rate", "payment currency"],
        "description": "Cross-border contracts should specify currency and exchange rate provisions",
    },

    # Anti-Corruption
    {
        "code": "ANTI-001", "title": "Anti-Corruption Provisions",
        "category": "Anti-Corruption", "severity": "high",
        "jurisdictions": ["US-Federal", "UK", "EU-GDPR"],
        "rule_type": "mandatory_inclusion",
        "required_keywords": ["anti-corruption", "anti-bribery", "fcpa", "uk bribery act"],
        "description": "International contracts should include anti-corruption compliance provisions",
    },
]


# ─── Compliance Check Schemas ───────────────────────────────────────────

class ComplianceRuleResult(BaseModel):
    """Result of checking a single compliance rule."""
    rule_code: str
    rule_title: str
    category: str
    severity: str
    status: str  # compliant, non_compliant, warning, not_applicable
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    remediation: Optional[str] = None
    affected_sections: List[str] = Field(default_factory=list)
    statute_reference: Optional[str] = None


class ComplianceCheckRequest(BaseModel):
    """Request schema for compliance checking."""
    contract_content: str
    contract_type: str
    jurisdiction: str
    additional_jurisdictions: List[str] = Field(default_factory=list)
    industry: str = "general"
    regulations: List[str] = Field(default_factory=list)  # Specific regulations to check
    llm_provider: Optional[str] = None


class ComplianceCheckResponse(BaseModel):
    """Response schema for compliance checking."""
    check_id: str
    overall_status: str  # compliant, non_compliant, partial
    compliance_score: float
    jurisdiction: str
    additional_jurisdictions_checked: List[str]
    total_rules_checked: int
    rules_passed: int
    rules_failed: int
    rules_warning: int
    rules_not_applicable: int
    results: List[ComplianceRuleResult]
    required_actions: List[str]
    recommendations: List[str]
    check_time_ms: int


# ─── Compliance Checker Service ──────────────────────────────────────────

class ComplianceChecker:
    """Service for multi-jurisdictional compliance checking."""

    def __init__(self):
        self.llm = llm_service
        self.rules = COMPLIANCE_RULES

    async def check_compliance(
        self,
        content: str = "",
        contract_type: str = "general",
        jurisdictions: List[str] = None,
        frameworks: List[str] = None,
        request: "ComplianceCheckRequest | None" = None,
    ) -> Dict[str, Any]:
        """Check compliance - accepts either keyword args or a request object.

        Returns a dict in the format expected by the routes.
        """
        if request is None:
            request = ComplianceCheckRequest(
                contract_content=content,
                contract_type=contract_type,
                jurisdiction=jurisdictions[0] if jurisdictions else "US-Federal",
                additional_jurisdictions=jurisdictions[1:] if jurisdictions and len(jurisdictions) > 1 else [],
                regulations=frameworks or [],
            )
        result = await self._check_compliance_internal(request)

        # Map to dict format for routes
        framework_rules: Dict[str, Dict[str, int]] = {}
        rule_results = []
        for r in result.results:
            rule_results.append({
                "rule_id": r.rule_code,
                "rule_name": r.rule_title,
                "framework": r.category.lower(),
                "category": r.category,
                "status": r.status,
                "severity": r.severity,
                "description": r.explanation,
                "finding": None,
                "recommendation": r.remediation,
                "clause_reference": None,
            })
            cat = r.category.lower()
            if cat not in framework_rules:
                framework_rules[cat] = {"passed": 0, "total": 0}
            if r.status != "not_applicable":
                framework_rules[cat]["total"] += 1
                if r.status == "compliant":
                    framework_rules[cat]["passed"] += 1

        framework_scores = {
            k: v["passed"] / max(v["total"], 1) for k, v in framework_rules.items()
        }

        return {
            "rule_results": rule_results,
            "overall_score": result.compliance_score,
            "framework_scores": framework_scores,
            "recommendations": result.recommendations,
        }

    async def _check_compliance_internal(
        self,
        request: ComplianceCheckRequest,
    ) -> ComplianceCheckResponse:
        """Perform comprehensive compliance check on a contract."""
        start_time = time.time()
        check_id = str(uuid.uuid4())

        logger.info(
            "Starting compliance check",
            check_id=check_id,
            jurisdiction=request.jurisdiction,
            contract_type=request.contract_type,
        )

        # Validate jurisdiction — filter unsupported ones instead of failing
        all_jurisdictions = [request.jurisdiction] + request.additional_jurisdictions
        valid_jurisdictions = [j for j in all_jurisdictions if j in settings.SUPPORTED_JURISDICTIONS]
        unknown = [j for j in all_jurisdictions if j not in settings.SUPPORTED_JURISDICTIONS]
        if unknown:
            logger.warning(f"Skipping unsupported jurisdictions: {unknown}")
        if not valid_jurisdictions:
            # Fallback to US-Federal if no valid jurisdictions
            valid_jurisdictions = ["US-Federal"]
            logger.info("No supported jurisdictions provided, defaulting to US-Federal")
        all_jurisdictions = valid_jurisdictions

        try:
            # Step 1: Filter applicable rules
            applicable_rules = self._filter_applicable_rules(
                all_jurisdictions, request.contract_type, request.regulations
            )

            # Step 2: Rule-based compliance check
            results = self._check_rules(
                request.contract_content,
                applicable_rules,
                request,
            )

            # Step 3: LLM-enhanced compliance check
            llm_results = await self._llm_compliance_check(request)
            results = self._enhance_with_llm(results, llm_results)

            # Step 4: Calculate scores
            passed = sum(1 for r in results if r.status == "compliant")
            failed = sum(1 for r in results if r.status == "non_compliant")
            warning = sum(1 for r in results if r.status == "warning")
            not_applicable = sum(1 for r in results if r.status == "not_applicable")

            total_applicable = len(results) - not_applicable
            compliance_score = passed / max(total_applicable, 1)

            # Overall status
            if failed > 0:
                overall_status = "non_compliant"
            elif warning > 0:
                overall_status = "partial"
            else:
                overall_status = "compliant"

            # Generate actions and recommendations
            required_actions = self._generate_required_actions(results)
            recommendations = self._generate_recommendations(results)

            check_time = int((time.time() - start_time) * 1000)

            response = ComplianceCheckResponse(
                check_id=check_id,
                overall_status=overall_status,
                compliance_score=round(compliance_score, 3),
                jurisdiction=request.jurisdiction,
                additional_jurisdictions_checked=request.additional_jurisdictions,
                total_rules_checked=len(results),
                rules_passed=passed,
                rules_failed=failed,
                rules_warning=warning,
                rules_not_applicable=not_applicable,
                results=results,
                required_actions=required_actions,
                recommendations=recommendations,
                check_time_ms=check_time,
            )

            logger.info(
                "Compliance check completed",
                check_id=check_id,
                overall_status=overall_status,
                compliance_score=round(compliance_score, 3),
                check_time_ms=check_time,
            )

            return response

        except JurisdictionNotSupportedError:
            raise
        except Exception as e:
            logger.error("Compliance check failed", check_id=check_id, error=str(e))
            raise

    def _filter_applicable_rules(
        self,
        jurisdictions: List[str],
        contract_type: str,
        specific_regulations: List[str],
    ) -> List[Dict[str, Any]]:
        """Filter rules applicable to the given jurisdictions and contract type."""
        applicable = []

        for rule in self.rules:
            # Check jurisdiction applicability
            rule_jurisdictions = rule.get("jurisdictions", [])
            if rule_jurisdictions and not any(j in rule_jurisdictions for j in jurisdictions):
                continue

            # Check contract type applicability
            rule_contract_types = rule.get("contract_types", [])
            if rule_contract_types and contract_type not in rule_contract_types:
                continue

            # Check specific regulation filter
            if specific_regulations:
                if rule["category"] not in specific_regulations and rule["code"] not in specific_regulations:
                    continue

            applicable.append(rule)

        return applicable

    def _check_rules(
        self,
        content: str,
        rules: List[Dict[str, Any]],
        request: ComplianceCheckRequest,
    ) -> List[ComplianceRuleResult]:
        """Check contract against applicable rules."""
        results = []
        content_lower = content.lower()

        for rule in rules:
            result = self._check_single_rule(content_lower, content, rule, request)
            results.append(result)

        return results

    def _check_single_rule(
        self,
        content_lower: str,
        content: str,
        rule: Dict[str, Any],
        request: ComplianceCheckRequest,
    ) -> ComplianceRuleResult:
        """Check a single compliance rule against the contract."""
        rule_type = rule.get("rule_type", "mandatory_inclusion")

        if rule_type == "mandatory_inclusion":
            return self._check_mandatory_inclusion(content_lower, rule)
        elif rule_type == "prohibited":
            return self._check_prohibited(content_lower, rule)
        elif rule_type == "conditional":
            return self._check_conditional(content_lower, rule, request)
        else:
            return ComplianceRuleResult(
                rule_code=rule["code"],
                rule_title=rule["title"],
                category=rule["category"],
                severity=rule["severity"],
                status="not_applicable",
                confidence=1.0,
                explanation="Rule type not recognized",
            )

    def _check_mandatory_inclusion(
        self,
        content_lower: str,
        rule: Dict[str, Any],
    ) -> ComplianceRuleResult:
        """Check if mandatory provisions are included."""
        required_keywords = rule.get("required_keywords", [])
        found_keywords = [kw for kw in required_keywords if kw.lower() in content_lower]
        coverage = len(found_keywords) / max(len(required_keywords), 1)

        if coverage >= 0.5:
            status = "compliant"
            explanation = (
                f"Contract includes required provisions. "
                f"Found: {', '.join(found_keywords)}."
            )
        elif coverage > 0:
            status = "warning"
            missing = [kw for kw in required_keywords if kw.lower() not in content_lower]
            explanation = (
                f"Contract partially addresses this requirement. "
                f"Missing provisions: {', '.join(missing[:3])}."
            )
        else:
            status = "non_compliant"
            explanation = (
                f"{rule['description']}. "
                f"None of the required provisions were found."
            )

        remediation = None
        if status != "compliant":
            remediation = (
                f"Add provisions addressing: {', '.join(required_keywords[:5])}. "
                f"Refer to {rule['category']} requirements."
            )

        return ComplianceRuleResult(
            rule_code=rule["code"],
            rule_title=rule["title"],
            category=rule["category"],
            severity=rule["severity"],
            status=status,
            confidence=0.85 if status == "compliant" else 0.9,
            explanation=explanation,
            remediation=remediation,
        )

    def _check_prohibited(
        self,
        content_lower: str,
        rule: Dict[str, Any],
    ) -> ComplianceRuleResult:
        """Check if prohibited provisions are absent."""
        prohibited_keywords = rule.get("prohibited_keywords", [])
        found_prohibited = [kw for kw in prohibited_keywords if kw.lower() in content_lower]

        if not found_prohibited:
            return ComplianceRuleResult(
                rule_code=rule["code"],
                rule_title=rule["title"],
                category=rule["category"],
                severity=rule["severity"],
                status="compliant",
                confidence=0.9,
                explanation="No prohibited provisions detected.",
            )
        else:
            return ComplianceRuleResult(
                rule_code=rule["code"],
                rule_title=rule["title"],
                category=rule["category"],
                severity=rule["severity"],
                status="non_compliant",
                confidence=0.95,
                explanation=(
                    f"Prohibited provisions detected: {', '.join(found_prohibited)}. "
                    f"{rule['description']}"
                ),
                remediation=f"Remove or modify the following prohibited provisions: {', '.join(found_prohibited)}.",
            )

    def _check_conditional(
        self,
        content_lower: str,
        rule: Dict[str, Any],
        request: ComplianceCheckRequest,
    ) -> ComplianceRuleResult:
        """Check conditional rules (only apply in certain contexts)."""
        # Check if the condition context exists in the contract
        trigger_keywords = rule.get("required_keywords", [])[:2]
        context_exists = any(kw.lower() in content_lower for kw in trigger_keywords)

        if not context_exists:
            return ComplianceRuleResult(
                rule_code=rule["code"],
                rule_title=rule["title"],
                category=rule["category"],
                severity=rule["severity"],
                status="not_applicable",
                confidence=0.8,
                explanation="The condition triggering this rule does not appear to be present in the contract.",
            )

        # If context exists, check for required provisions
        all_keywords = rule.get("required_keywords", [])
        found = [kw for kw in all_keywords if kw.lower() in content_lower]
        coverage = len(found) / max(len(all_keywords), 1)

        if coverage >= 0.5:
            status = "compliant"
            explanation = f"Required conditional provisions are present."
        elif coverage > 0:
            status = "warning"
            explanation = f"Conditional provisions are partially addressed."
        else:
            status = "non_compliant"
            explanation = f"Context requires these provisions but they are missing: {rule['description']}"

        return ComplianceRuleResult(
            rule_code=rule["code"],
            rule_title=rule["title"],
            category=rule["category"],
            severity=rule["severity"],
            status=status,
            confidence=0.75,
            explanation=explanation,
            remediation=f"Add required provisions for {rule['category']} compliance." if status != "compliant" else None,
        )

    async def _llm_compliance_check(self, request: ComplianceCheckRequest) -> Dict[str, Any]:
        """Enhanced compliance check using LLM."""
        try:
            regulations = request.regulations or ["General Contract Law"]
            result = await self.llm.check_compliance(
                contract_content=request.contract_content,
                contract_type=request.contract_type,
                jurisdiction=request.jurisdiction,
                regulations=regulations,
                provider=request.llm_provider,
            )
            return result
        except Exception as e:
            logger.warning(f"LLM compliance check failed: {e}")
            return {}

    def _enhance_with_llm(
        self,
        results: List[ComplianceRuleResult],
        llm_results: Dict[str, Any],
    ) -> List[ComplianceRuleResult]:
        """Enhance rule-based results with LLM analysis."""
        llm_checks = llm_results.get("checks", [])

        for llm_check in llm_checks:
            # Find matching rule result
            matched = False
            for result in results:
                if (llm_check.get("rule", "").lower() in result.rule_title.lower() or
                    result.category.lower() in llm_check.get("rule", "").lower()):
                    # Enhance explanation
                    if llm_check.get("explanation"):
                        result.explanation += f" AI analysis: {llm_check['explanation']}"
                    matched = True
                    break

            if not matched and llm_check.get("rule"):
                # Add new check from LLM
                results.append(ComplianceRuleResult(
                    rule_code=f"AI-{len(results):03d}",
                    rule_title=llm_check.get("rule", "AI-Identified Rule"),
                    category=llm_check.get("category", "AI Analysis"),
                    severity=llm_check.get("severity", "medium"),
                    status=llm_check.get("status", "warning"),
                    confidence=0.7,
                    explanation=llm_check.get("explanation", "Identified by AI compliance analysis"),
                    remediation=llm_check.get("remediation"),
                ))

        return results

    def _generate_required_actions(self, results: List[ComplianceRuleResult]) -> List[str]:
        """Generate list of required actions for non-compliant results."""
        actions = []
        for result in results:
            if result.status == "non_compliant" and result.remediation:
                actions.append(
                    f"[{result.severity.upper()}] {result.rule_title}: {result.remediation}"
                )
        return sorted(actions, key=lambda x: (
            0 if "[CRITICAL]" in x else 1 if "[HIGH]" in x else 2
        ))

    def _generate_recommendations(self, results: List[ComplianceRuleResult]) -> List[str]:
        """Generate recommendations including warnings."""
        recommendations = []
        for result in results:
            if result.status == "warning":
                recommendations.append(
                    f"Review {result.rule_title} ({result.category}): {result.explanation}"
                )
        return recommendations[:10]

    def get_jurisdiction_requirements(self, jurisdiction: str) -> Dict[str, Any]:
        """Get compliance requirements for a specific jurisdiction."""
        applicable_rules = [
            rule for rule in self.rules
            if not rule.get("jurisdictions") or jurisdiction in rule["jurisdictions"]
        ]

        categories = {}
        for rule in applicable_rules:
            cat = rule["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "code": rule["code"],
                "title": rule["title"],
                "severity": rule["severity"],
                "description": rule["description"],
            })

        return {
            "jurisdiction": jurisdiction,
            "total_rules": len(applicable_rules),
            "categories": categories,
        }


# Singleton instance
compliance_checker = ComplianceChecker()
