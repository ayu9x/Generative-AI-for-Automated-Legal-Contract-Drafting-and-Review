"""Risk Analysis Engine - Comprehensive contract risk assessment with explainable AI."""

import uuid
import time
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

import structlog
from pydantic import BaseModel, Field

from app.config import settings
from app.core.exceptions import RiskAnalysisError
from app.services.llm_service import llm_service

logger = structlog.get_logger(__name__)


# ─── Risk Factor Definitions ────────────────────────────────────────────

RISK_FACTORS: List[Dict[str, Any]] = [
    # Financial Risks
    {"code": "FIN-001", "name": "Unlimited Liability Exposure", "category": "financial", "severity": "critical",
     "keywords": ["unlimited liability", "no cap", "without limitation"], "absence_risk": False,
     "description": "Contract lacks cap on financial liability"},
    {"code": "FIN-002", "name": "Inadequate Payment Terms", "category": "financial", "severity": "high",
     "keywords": ["net 90", "net 120", "upon completion only"], "absence_risk": False,
     "description": "Payment terms unfavorable or unclear"},
    {"code": "FIN-003", "name": "Missing Penalty Provisions", "category": "financial", "severity": "medium",
     "keywords": ["penalty", "liquidated damages", "late fee"], "absence_risk": True,
     "description": "No provisions for penalties or liquidated damages"},
    {"code": "FIN-004", "name": "No Price Adjustment Mechanism", "category": "financial", "severity": "medium",
     "keywords": ["price adjustment", "escalation", "cpi", "inflation"], "absence_risk": True,
     "description": "Long-term contracts without price adjustment mechanisms"},
    {"code": "FIN-005", "name": "Uncapped Indemnification", "category": "financial", "severity": "critical",
     "keywords": ["indemnify and hold harmless", "full indemnification"], "absence_risk": False,
     "description": "Indemnification obligations without monetary limits"},

    # Regulatory Risks
    {"code": "REG-001", "name": "Missing Data Protection Clause", "category": "regulatory", "severity": "critical",
     "keywords": ["data protection", "gdpr", "ccpa", "personal data", "privacy"], "absence_risk": True,
     "description": "No data protection or privacy provisions"},
    {"code": "REG-002", "name": "Non-Compliant Export Controls", "category": "regulatory", "severity": "high",
     "keywords": ["export control", "itar", "ear", "sanctions"], "absence_risk": True,
     "description": "Missing export control compliance provisions"},
    {"code": "REG-003", "name": "Anti-Bribery Missing", "category": "regulatory", "severity": "high",
     "keywords": ["anti-bribery", "fcpa", "uk bribery act", "corruption"], "absence_risk": True,
     "description": "No anti-corruption or anti-bribery clause"},
    {"code": "REG-004", "name": "HIPAA Non-Compliance", "category": "regulatory", "severity": "critical",
     "keywords": ["hipaa", "phi", "protected health information", "baa"], "absence_risk": True,
     "description": "Healthcare data handling without HIPAA provisions"},
    {"code": "REG-005", "name": "SOX Compliance Gap", "category": "regulatory", "severity": "high",
     "keywords": ["sox", "sarbanes-oxley", "internal controls", "financial reporting"], "absence_risk": True,
     "description": "Financial contracts lacking SOX compliance provisions"},

    # Operational Risks
    {"code": "OPS-001", "name": "Vague Service Levels", "category": "operational", "severity": "high",
     "keywords": ["best efforts", "commercially reasonable", "as soon as practicable"], "absence_risk": False,
     "description": "Service level commitments are vague or unenforceable"},
    {"code": "OPS-002", "name": "Missing SLA Remedies", "category": "operational", "severity": "high",
     "keywords": ["service credit", "sla penalty", "service level remedy"], "absence_risk": True,
     "description": "No remedies for SLA breaches"},
    {"code": "OPS-003", "name": "Inadequate Business Continuity", "category": "operational", "severity": "medium",
     "keywords": ["disaster recovery", "business continuity", "backup", "redundancy"], "absence_risk": True,
     "description": "No business continuity or disaster recovery provisions"},
    {"code": "OPS-004", "name": "Key Person Dependency", "category": "operational", "severity": "medium",
     "keywords": ["key person", "named individual", "specific personnel"], "absence_risk": False,
     "description": "Contract performance depends on specific individuals"},

    # Legal Liability
    {"code": "LIA-001", "name": "Broad Representations", "category": "legal_liability", "severity": "high",
     "keywords": ["represents and warrants", "warrants that", "represents that"], "absence_risk": False,
     "description": "Overly broad representations and warranties"},
    {"code": "LIA-002", "name": "Missing Limitation of Liability", "category": "legal_liability", "severity": "critical",
     "keywords": ["limitation of liability", "liability cap", "aggregate liability"], "absence_risk": True,
     "description": "No limitation of liability clause"},
    {"code": "LIA-003", "name": "Consequential Damages Risk", "category": "legal_liability", "severity": "high",
     "keywords": ["consequential damages", "indirect damages", "lost profits", "special damages"], "absence_risk": True,
     "description": "No exclusion of consequential/indirect damages"},
    {"code": "LIA-004", "name": "Joint and Several Liability", "category": "legal_liability", "severity": "high",
     "keywords": ["joint and several", "jointly and severally"], "absence_risk": False,
     "description": "Exposure to joint and several liability"},

    # IP Risks
    {"code": "IP-001", "name": "Unclear IP Ownership", "category": "intellectual_property", "severity": "critical",
     "keywords": ["intellectual property", "ownership", "work product", "work for hire"], "absence_risk": True,
     "description": "Intellectual property ownership is unclear or missing"},
    {"code": "IP-002", "name": "Broad IP License Grant", "category": "intellectual_property", "severity": "high",
     "keywords": ["perpetual", "irrevocable", "worldwide", "sublicensable"], "absence_risk": False,
     "description": "Overly broad intellectual property license granted"},
    {"code": "IP-003", "name": "No IP Indemnification", "category": "intellectual_property", "severity": "high",
     "keywords": ["ip indemnification", "infringement indemnity", "patent indemnity"], "absence_risk": True,
     "description": "Missing IP infringement indemnification"},

    # Data Privacy Risks
    {"code": "DPR-001", "name": "No Breach Notification", "category": "data_privacy", "severity": "critical",
     "keywords": ["breach notification", "data breach", "security incident"], "absence_risk": True,
     "description": "No data breach notification requirements"},
    {"code": "DPR-002", "name": "Cross-Border Data Transfer", "category": "data_privacy", "severity": "high",
     "keywords": ["data transfer", "cross-border", "international transfer", "adequacy"], "absence_risk": True,
     "description": "International data transfers without adequate safeguards"},
    {"code": "DPR-003", "name": "No Data Retention Policy", "category": "data_privacy", "severity": "medium",
     "keywords": ["data retention", "data deletion", "data destruction"], "absence_risk": True,
     "description": "Missing data retention and deletion provisions"},

    # Termination Risks
    {"code": "TRM-001", "name": "Inadequate Termination Rights", "category": "termination", "severity": "high",
     "keywords": ["termination for convenience", "right to terminate"], "absence_risk": True,
     "description": "Inadequate or missing termination rights"},
    {"code": "TRM-002", "name": "No Cure Period", "category": "termination", "severity": "medium",
     "keywords": ["cure period", "right to cure", "opportunity to cure"], "absence_risk": True,
     "description": "No cure period before termination for cause"},
    {"code": "TRM-003", "name": "Unclear Post-Termination", "category": "termination", "severity": "high",
     "keywords": ["post-termination", "survival", "surviving provisions"], "absence_risk": True,
     "description": "Unclear post-termination obligations"},

    # Confidentiality Risks
    {"code": "CNF-001", "name": "Overly Broad Confidentiality", "category": "confidentiality", "severity": "medium",
     "keywords": ["all information", "any and all", "without limitation"], "absence_risk": False,
     "description": "Confidentiality definition is overly broad"},
    {"code": "CNF-002", "name": "No Confidentiality Exceptions", "category": "confidentiality", "severity": "medium",
     "keywords": ["exceptions", "exclusions", "publicly available", "independently developed"], "absence_risk": True,
     "description": "Missing standard confidentiality exceptions"},
    {"code": "CNF-003", "name": "Perpetual Confidentiality", "category": "confidentiality", "severity": "medium",
     "keywords": ["perpetual confidentiality", "indefinite", "forever"], "absence_risk": False,
     "description": "Unreasonable confidentiality duration"},

    # Dispute Resolution
    {"code": "DSP-001", "name": "No Dispute Mechanism", "category": "dispute_resolution", "severity": "high",
     "keywords": ["arbitration", "mediation", "dispute resolution"], "absence_risk": True,
     "description": "No dispute resolution mechanism specified"},
    {"code": "DSP-002", "name": "Unfavorable Venue", "category": "dispute_resolution", "severity": "medium",
     "keywords": ["exclusive jurisdiction", "venue", "forum selection"], "absence_risk": False,
     "description": "Dispute resolution venue may be unfavorable"},
    {"code": "DSP-003", "name": "No Attorneys Fees", "category": "dispute_resolution", "severity": "low",
     "keywords": ["attorneys' fees", "attorney fees", "legal costs", "prevailing party"], "absence_risk": True,
     "description": "No provision for recovery of attorneys' fees"},

    # Force Majeure
    {"code": "FM-001", "name": "No Force Majeure", "category": "force_majeure", "severity": "high",
     "keywords": ["force majeure", "act of god", "unforeseeable"], "absence_risk": True,
     "description": "Missing force majeure clause"},
    {"code": "FM-002", "name": "Narrow Force Majeure", "category": "force_majeure", "severity": "medium",
     "keywords": ["pandemic", "epidemic", "cyber attack", "government action"], "absence_risk": False,
     "description": "Force majeure clause doesn't cover modern risks (pandemics, cyber)"},

    # Non-Compete
    {"code": "NC-001", "name": "Overly Broad Non-Compete", "category": "non_compete", "severity": "high",
     "keywords": ["non-compete", "non-competition", "restrictive covenant"], "absence_risk": False,
     "description": "Non-compete provisions may be unenforceable due to breadth"},
    {"code": "NC-002", "name": "Excessive Non-Compete Duration", "category": "non_compete", "severity": "high",
     "keywords": ["years", "months", "non-compete period"], "absence_risk": False,
     "description": "Non-compete duration exceeds typical enforceability limits"},
]


# ─── Risk Analysis Schemas ──────────────────────────────────────────────

class RiskFactorResult(BaseModel):
    """Individual risk factor analysis result."""
    factor_code: str
    factor_name: str
    category: str
    severity: str
    score: float = Field(ge=0.0, le=1.0)
    detected: bool
    explanation: str
    evidence: List[str] = Field(default_factory=list)
    affected_clauses: List[str] = Field(default_factory=list)
    remediation: Optional[str] = None
    legal_precedent: Optional[str] = None
    market_comparison: Optional[str] = None


class RiskAnalysisRequest(BaseModel):
    """Request schema for risk analysis."""
    contract_content: str
    contract_type: str
    jurisdiction: str
    industry: str = "general"
    party_perspective: str = "neutral"  # neutral, party_a, party_b
    include_precedents: bool = True
    custom_risk_factors: List[str] = Field(default_factory=list)
    llm_provider: Optional[str] = None


class RiskAnalysisResponse(BaseModel):
    """Response schema for risk analysis."""
    assessment_id: str
    overall_risk_score: float
    risk_level: str
    confidence_score: float
    category_scores: Dict[str, float]
    risk_factors: List[RiskFactorResult]
    executive_summary: str
    key_findings: List[str]
    recommendations: List[str]
    mitigations: List[Dict[str, str]]
    statistics: Dict[str, Any]
    analysis_time_ms: int


# ─── Risk Analysis Engine ───────────────────────────────────────────────

class RiskAnalyzer:
    """Engine for comprehensive contract risk analysis."""

    def __init__(self):
        self.llm = llm_service
        self.risk_factors = RISK_FACTORS

    async def analyze(
        self,
        content: str,
        contract_type: str = "general",
        jurisdiction: str = "US-Federal",
    ) -> Dict[str, Any]:
        """Convenience method returning dict format for route compatibility."""
        request = RiskAnalysisRequest(
            contract_content=content,
            contract_type=contract_type,
            jurisdiction=jurisdiction,
        )
        result = await self.analyze_contract(request)
        return {
            "overall_risk_score": result.overall_risk_score,
            "risk_level": result.risk_level,
            "risk_factors": [
                {
                    "category": rf.category,
                    "name": rf.factor_name,
                    "severity": rf.severity,
                    "description": rf.explanation,
                    "recommendation": rf.remediation or "Review required",
                    "clause_reference": None,
                    "confidence": rf.score,
                }
                for rf in result.risk_factors if rf.detected
            ],
            "category_scores": result.category_scores,
            "executive_summary": result.executive_summary,
            "recommendations": result.recommendations,
        }

    async def analyze_contract(
        self,
        request: RiskAnalysisRequest,
    ) -> RiskAnalysisResponse:
        """Perform comprehensive risk analysis on a contract."""
        start_time = time.time()
        assessment_id = str(uuid.uuid4())

        logger.info(
            "Starting risk analysis",
            assessment_id=assessment_id,
            contract_type=request.contract_type,
            jurisdiction=request.jurisdiction,
        )

        try:
            # Step 1: Rule-based analysis
            rule_based_results = self._rule_based_analysis(
                request.contract_content,
                request.contract_type,
                request.jurisdiction,
            )

            # Step 2: LLM-enhanced analysis
            llm_results = await self._llm_analysis(request)

            # Step 3: Merge and score results
            merged_results = self._merge_results(rule_based_results, llm_results)

            # Step 4: Calculate scores
            overall_score = self._calculate_overall_score(merged_results)
            category_scores = self._calculate_category_scores(merged_results)
            risk_level = self._determine_risk_level(overall_score)

            # Step 5: Generate executive summary
            summary = self._generate_executive_summary(
                merged_results, overall_score, risk_level, request
            )

            # Step 6: Generate recommendations
            recommendations = self._generate_recommendations(merged_results)
            mitigations = self._generate_mitigations(merged_results)

            # Step 7: Key findings
            key_findings = self._extract_key_findings(merged_results)

            # Statistics
            total_factors = len(merged_results)
            high_risk = sum(1 for r in merged_results if r.score >= settings.RISK_SCORE_THRESHOLD_HIGH)
            medium_risk = sum(
                1 for r in merged_results
                if settings.RISK_SCORE_THRESHOLD_MEDIUM <= r.score < settings.RISK_SCORE_THRESHOLD_HIGH
            )
            low_risk = sum(1 for r in merged_results if r.score < settings.RISK_SCORE_THRESHOLD_MEDIUM and r.detected)

            analysis_time = int((time.time() - start_time) * 1000)

            response = RiskAnalysisResponse(
                assessment_id=assessment_id,
                overall_risk_score=round(overall_score, 3),
                risk_level=risk_level,
                confidence_score=0.92,
                category_scores=category_scores,
                risk_factors=merged_results,
                executive_summary=summary,
                key_findings=key_findings,
                recommendations=recommendations,
                mitigations=mitigations,
                statistics={
                    "total_factors_analyzed": total_factors,
                    "high_risk_count": high_risk,
                    "medium_risk_count": medium_risk,
                    "low_risk_count": low_risk,
                    "not_detected_count": sum(1 for r in merged_results if not r.detected),
                    "categories_analyzed": len(category_scores),
                },
                analysis_time_ms=analysis_time,
            )

            logger.info(
                "Risk analysis completed",
                assessment_id=assessment_id,
                overall_score=overall_score,
                risk_level=risk_level,
                analysis_time_ms=analysis_time,
            )

            return response

        except Exception as e:
            logger.error("Risk analysis failed", assessment_id=assessment_id, error=str(e))
            raise RiskAnalysisError(f"Risk analysis failed: {str(e)}")

    def _rule_based_analysis(
        self,
        content: str,
        contract_type: str,
        jurisdiction: str,
    ) -> List[RiskFactorResult]:
        """Perform rule-based risk analysis using keyword matching and patterns."""
        results = []
        content_lower = content.lower()

        for factor in self.risk_factors:
            # Check if factor applies to this contract type
            if factor.get("contract_types") and contract_type not in factor["contract_types"]:
                continue

            # Check if factor applies to this jurisdiction
            if factor.get("jurisdictions") and jurisdiction not in factor["jurisdictions"]:
                continue

            # Keyword detection
            keywords = factor.get("keywords", [])
            found_keywords = [kw for kw in keywords if kw.lower() in content_lower]
            detected = len(found_keywords) > 0

            # Handle absence risk (risk when clause is MISSING)
            if factor.get("absence_risk", False):
                detected = not detected  # Flip: risk exists if keywords are NOT found
                if detected:
                    evidence = [f"Missing provisions related to: {', '.join(keywords)}"]
                else:
                    evidence = [f"Found provisions containing: {', '.join(found_keywords)}"]
            else:
                evidence = self._extract_evidence(content, found_keywords)

            # Calculate score
            score = self._calculate_factor_score(factor, detected, found_keywords, content)

            # Generate explanation
            explanation = self._generate_factor_explanation(factor, detected, found_keywords)

            results.append(RiskFactorResult(
                factor_code=factor["code"],
                factor_name=factor["name"],
                category=factor["category"],
                severity=factor["severity"],
                score=score,
                detected=detected,
                explanation=explanation,
                evidence=evidence[:3],  # Limit evidence snippets
                affected_clauses=[],
                remediation=self._get_remediation(factor, detected),
            ))

        return results

    async def _llm_analysis(self, request: RiskAnalysisRequest) -> Dict[str, Any]:
        """Perform LLM-enhanced risk analysis."""
        try:
            result = await self.llm.analyze_risks(
                contract_content=request.contract_content,
                contract_type=request.contract_type,
                jurisdiction=request.jurisdiction,
                provider=request.llm_provider,
            )
            return result
        except Exception as e:
            logger.warning(f"LLM analysis failed, proceeding with rule-based only: {e}")
            return {}

    def _merge_results(
        self,
        rule_results: List[RiskFactorResult],
        llm_results: Dict[str, Any],
    ) -> List[RiskFactorResult]:
        """Merge rule-based and LLM results."""
        merged = list(rule_results)

        # Enhance with LLM findings
        llm_factors = llm_results.get("risk_factors", [])
        for llm_factor in llm_factors:
            # Find matching rule-based result
            matched = False
            for result in merged:
                if (result.category == llm_factor.get("category") or
                    any(kw in llm_factor.get("factor", "").lower()
                        for kw in result.factor_name.lower().split())):
                    # Enhance existing result
                    if llm_factor.get("precedent"):
                        result.legal_precedent = llm_factor["precedent"]
                    if llm_factor.get("remediation"):
                        result.remediation = llm_factor["remediation"]
                    # Adjust score with LLM confidence
                    llm_score = llm_factor.get("score", result.score)
                    result.score = round((result.score + llm_score) / 2, 3)
                    matched = True
                    break

            if not matched and llm_factor.get("factor"):
                # Add new factor from LLM
                merged.append(RiskFactorResult(
                    factor_code=f"LLM-{len(merged):03d}",
                    factor_name=llm_factor.get("factor", "LLM Detected Risk"),
                    category=llm_factor.get("category", "general"),
                    severity=self._score_to_severity(llm_factor.get("score", 0.5)),
                    score=llm_factor.get("score", 0.5),
                    detected=True,
                    explanation=llm_factor.get("explanation", "Identified by AI analysis"),
                    evidence=[],
                    remediation=llm_factor.get("remediation"),
                    legal_precedent=llm_factor.get("precedent"),
                ))

        return merged

    def _calculate_factor_score(
        self,
        factor: Dict[str, Any],
        detected: bool,
        found_keywords: List[str],
        content: str,
    ) -> float:
        """Calculate risk score for a specific factor."""
        if not detected:
            return 0.0

        # Base score from severity
        severity_scores = {
            "critical": 0.9,
            "high": 0.7,
            "medium": 0.5,
            "low": 0.25,
        }
        base_score = severity_scores.get(factor["severity"], 0.5)

        # Adjust based on keyword match confidence
        keyword_ratio = len(found_keywords) / max(len(factor.get("keywords", [""])), 1)
        confidence_adjustment = min(keyword_ratio * 0.2, 0.1)

        return min(round(base_score + confidence_adjustment, 3), 1.0)

    def _calculate_overall_score(self, results: List[RiskFactorResult]) -> float:
        """Calculate overall risk score from individual factors."""
        if not results:
            return 0.0

        detected_results = [r for r in results if r.detected]
        if not detected_results:
            return 0.0

        # Weighted average based on severity
        severity_weights = {"critical": 3.0, "high": 2.0, "medium": 1.5, "low": 1.0}
        total_weight = 0.0
        weighted_sum = 0.0

        for result in detected_results:
            weight = severity_weights.get(result.severity, 1.0)
            weighted_sum += result.score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(weighted_sum / total_weight, 3)

    def _calculate_category_scores(self, results: List[RiskFactorResult]) -> Dict[str, float]:
        """Calculate risk scores per category."""
        categories: Dict[str, List[float]] = {}
        for result in results:
            if result.detected:
                if result.category not in categories:
                    categories[result.category] = []
                categories[result.category].append(result.score)

        return {
            cat: round(sum(scores) / len(scores), 3) if scores else 0.0
            for cat, scores in categories.items()
        }

    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level from overall score."""
        if score >= settings.RISK_SCORE_THRESHOLD_HIGH:
            return "critical" if score >= 0.85 else "high"
        elif score >= settings.RISK_SCORE_THRESHOLD_MEDIUM:
            return "medium"
        elif score >= settings.RISK_SCORE_THRESHOLD_LOW:
            return "low"
        return "minimal"

    def _extract_evidence(self, content: str, keywords: List[str]) -> List[str]:
        """Extract evidence snippets from contract content."""
        evidence = []
        for keyword in keywords:
            # Find keyword in content and extract surrounding context
            idx = content.lower().find(keyword.lower())
            if idx >= 0:
                start = max(0, idx - 100)
                end = min(len(content), idx + len(keyword) + 100)
                snippet = content[start:end].strip()
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
                evidence.append(snippet)
        return evidence

    def _generate_factor_explanation(
        self,
        factor: Dict[str, Any],
        detected: bool,
        found_keywords: List[str],
    ) -> str:
        """Generate human-readable explanation for a risk factor."""
        if detected:
            if factor.get("absence_risk"):
                return (
                    f"{factor['name']}: {factor['description']}. "
                    f"This is a {factor['severity']} severity risk. "
                    f"The contract is missing provisions that typically address: "
                    f"{', '.join(factor.get('keywords', []))}."
                )
            else:
                return (
                    f"{factor['name']}: {factor['description']}. "
                    f"This is a {factor['severity']} severity risk. "
                    f"Detected indicators: {', '.join(found_keywords)}."
                )
        return f"{factor['name']}: No risk detected in this area."

    def _get_remediation(self, factor: Dict[str, Any], detected: bool) -> Optional[str]:
        """Get remediation advice for a detected risk."""
        if not detected:
            return None

        remediations = {
            "financial": "Consider adding appropriate financial protections, liability caps, or escrow arrangements.",
            "regulatory": "Add required regulatory compliance provisions for the applicable jurisdiction.",
            "operational": "Include specific, measurable service levels with defined remedies.",
            "legal_liability": "Add limitation of liability clause with appropriate caps and exclusions.",
            "intellectual_property": "Clarify IP ownership, licensing terms, and infringement indemnification.",
            "data_privacy": "Include comprehensive data protection provisions aligned with applicable regulations.",
            "termination": "Add clear termination rights with appropriate notice and cure periods.",
            "confidentiality": "Refine confidentiality scope, exceptions, and duration to be reasonable.",
            "dispute_resolution": "Include structured dispute resolution mechanism (mediation, then arbitration).",
            "force_majeure": "Add comprehensive force majeure clause covering modern risks.",
            "non_compete": "Ensure non-compete is reasonable in scope, geography, and duration.",
            "indemnification": "Set appropriate indemnification caps and procedural requirements.",
        }

        return remediations.get(factor["category"], "Review and address the identified risk with legal counsel.")

    def _generate_executive_summary(
        self,
        results: List[RiskFactorResult],
        overall_score: float,
        risk_level: str,
        request: RiskAnalysisRequest,
    ) -> str:
        """Generate an executive summary of the risk analysis."""
        detected = [r for r in results if r.detected]
        critical = [r for r in detected if r.severity == "critical"]
        high = [r for r in detected if r.severity == "high"]

        summary = (
            f"Risk Assessment Summary for {request.contract_type.replace('_', ' ').title()} "
            f"under {request.jurisdiction} jurisdiction.\n\n"
            f"Overall Risk Level: {risk_level.upper()} (Score: {overall_score:.1%})\n\n"
            f"Analysis identified {len(detected)} risk factors out of {len(results)} evaluated. "
        )

        if critical:
            summary += (
                f"\n\nCRITICAL RISKS ({len(critical)}): "
                f"{'; '.join([r.factor_name for r in critical])}. "
                f"These require immediate attention before contract execution."
            )

        if high:
            summary += (
                f"\n\nHIGH RISKS ({len(high)}): "
                f"{'; '.join([r.factor_name for r in high])}. "
                f"These should be addressed during contract negotiation."
            )

        if not critical and not high:
            summary += "No critical or high-severity risks were identified."

        return summary

    def _extract_key_findings(self, results: List[RiskFactorResult]) -> List[str]:
        """Extract key findings from analysis results."""
        findings = []
        critical_high = [r for r in results if r.detected and r.severity in ("critical", "high")]

        for result in sorted(critical_high, key=lambda x: x.score, reverse=True)[:10]:
            findings.append(f"[{result.severity.upper()}] {result.factor_name}: {result.explanation}")

        return findings

    def _generate_recommendations(self, results: List[RiskFactorResult]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        detected = [r for r in results if r.detected and r.remediation]

        for result in sorted(detected, key=lambda x: x.score, reverse=True)[:8]:
            recommendations.append(
                f"Address {result.factor_name} ({result.severity}): {result.remediation}"
            )

        return recommendations

    def _generate_mitigations(self, results: List[RiskFactorResult]) -> List[Dict[str, str]]:
        """Generate risk mitigation strategies."""
        mitigations = []
        critical_high = [r for r in results if r.detected and r.severity in ("critical", "high")]

        for result in critical_high[:10]:
            mitigations.append({
                "risk": result.factor_name,
                "category": result.category,
                "severity": result.severity,
                "mitigation": result.remediation or "Consult legal counsel for appropriate mitigation.",
                "priority": "immediate" if result.severity == "critical" else "high",
            })

        return mitigations

    def _score_to_severity(self, score: float) -> str:
        """Convert a numeric score to severity level."""
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        return "low"


# Singleton instance
risk_analyzer = RiskAnalyzer()
