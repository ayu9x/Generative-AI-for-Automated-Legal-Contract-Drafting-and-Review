"""Custom exception classes for the Legal Contract AI System."""

from typing import Optional, Dict, Any


class LegalContractBaseException(Exception):
    """Base exception for all legal contract system errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


# ─── Authentication & Authorization ─────────────────────────────────────

class AuthenticationError(LegalContractBaseException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(message, "AUTH_ERROR", details, 401)


class AuthorizationError(LegalContractBaseException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict] = None):
        super().__init__(message, "FORBIDDEN", details, 403)


class TokenExpiredError(LegalContractBaseException):
    """Raised when authentication token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, "TOKEN_EXPIRED", {}, 401)


# ─── Contract Errors ────────────────────────────────────────────────────

class ContractNotFoundError(LegalContractBaseException):
    """Raised when a contract is not found."""

    def __init__(self, contract_id: str):
        super().__init__(
            f"Contract not found: {contract_id}",
            "CONTRACT_NOT_FOUND",
            {"contract_id": contract_id},
            404,
        )


class ContractGenerationError(LegalContractBaseException):
    """Raised when contract generation fails."""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, "GENERATION_ERROR", details, 500)


class ContractValidationError(LegalContractBaseException):
    """Raised when contract validation fails."""

    def __init__(self, message: str, validation_errors: Optional[list] = None):
        super().__init__(
            message,
            "VALIDATION_ERROR",
            {"validation_errors": validation_errors or []},
            422,
        )


class TemplateNotFoundError(LegalContractBaseException):
    """Raised when a contract template is not found."""

    def __init__(self, template_id: str):
        super().__init__(
            f"Template not found: {template_id}",
            "TEMPLATE_NOT_FOUND",
            {"template_id": template_id},
            404,
        )


# ─── Compliance Errors ──────────────────────────────────────────────────

class ComplianceViolationError(LegalContractBaseException):
    """Raised when a compliance violation is detected."""

    def __init__(self, violations: list, jurisdiction: str):
        super().__init__(
            f"Compliance violations detected in {jurisdiction}",
            "COMPLIANCE_VIOLATION",
            {"violations": violations, "jurisdiction": jurisdiction},
            422,
        )


class JurisdictionNotSupportedError(LegalContractBaseException):
    """Raised when a jurisdiction is not supported."""

    def __init__(self, jurisdiction: str):
        super().__init__(
            f"Jurisdiction not supported: {jurisdiction}",
            "JURISDICTION_NOT_SUPPORTED",
            {"jurisdiction": jurisdiction},
            400,
        )


# ─── Risk Analysis Errors ───────────────────────────────────────────────

class RiskAnalysisError(LegalContractBaseException):
    """Raised when risk analysis encounters an error."""

    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, "RISK_ANALYSIS_ERROR", details, 500)


class HighRiskContractError(LegalContractBaseException):
    """Raised when a contract exceeds acceptable risk thresholds."""

    def __init__(self, risk_score: float, risk_factors: list):
        super().__init__(
            f"Contract risk score ({risk_score}) exceeds threshold",
            "HIGH_RISK",
            {"risk_score": risk_score, "risk_factors": risk_factors},
            422,
        )


# ─── LLM Errors ─────────────────────────────────────────────────────────

class LLMServiceError(LegalContractBaseException):
    """Raised when LLM service encounters an error."""

    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(
            message,
            "LLM_ERROR",
            {"provider": provider},
            503,
        )


class LLMRateLimitError(LegalContractBaseException):
    """Raised when LLM rate limit is exceeded."""

    def __init__(self, provider: str, retry_after: int = 60):
        super().__init__(
            f"Rate limit exceeded for {provider}",
            "LLM_RATE_LIMIT",
            {"provider": provider, "retry_after": retry_after},
            429,
        )


# ─── Document Errors ────────────────────────────────────────────────────

class DocumentParsingError(LegalContractBaseException):
    """Raised when document parsing fails."""

    def __init__(self, message: str, file_type: str = "unknown"):
        super().__init__(
            message,
            "DOCUMENT_PARSE_ERROR",
            {"file_type": file_type},
            400,
        )


class DocumentTooLargeError(LegalContractBaseException):
    """Raised when document exceeds size limits."""

    def __init__(self, size_mb: float, max_size_mb: int):
        super().__init__(
            f"Document size ({size_mb}MB) exceeds limit ({max_size_mb}MB)",
            "DOCUMENT_TOO_LARGE",
            {"size_mb": size_mb, "max_size_mb": max_size_mb},
            413,
        )


# ─── Version Control Errors ─────────────────────────────────────────────

class VersionConflictError(LegalContractBaseException):
    """Raised when a version conflict occurs during editing."""

    def __init__(self, contract_id: str, current_version: int, attempted_version: int):
        super().__init__(
            "Version conflict detected",
            "VERSION_CONFLICT",
            {
                "contract_id": contract_id,
                "current_version": current_version,
                "attempted_version": attempted_version,
            },
            409,
        )


class BranchNotFoundError(LegalContractBaseException):
    """Raised when a branch is not found."""

    def __init__(self, branch_name: str):
        super().__init__(
            f"Branch not found: {branch_name}",
            "BRANCH_NOT_FOUND",
            {"branch_name": branch_name},
            404,
        )


# ─── Encryption Errors ──────────────────────────────────────────────────

class EncryptionError(LegalContractBaseException):
    """Raised when encryption/decryption fails."""

    def __init__(self, operation: str = "encryption"):
        super().__init__(
            f"Data {operation} failed",
            "ENCRYPTION_ERROR",
            {"operation": operation},
            500,
        )
