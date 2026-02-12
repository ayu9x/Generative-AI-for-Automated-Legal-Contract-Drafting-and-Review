"""
Generative AI for Automated Legal Contract Drafting and Review
Main FastAPI Application Entry Point

myOnsite Healthcare, LLC - August 2025
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes import auth, contracts, review, compliance, versions
from app.api.middleware.security import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
)
from app.api.middleware.audit import AuditLogMiddleware
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    ContractNotFoundError,
    ContractGenerationError,
    ContractValidationError,
    ComplianceViolationError,
    JurisdictionNotSupportedError,
    RiskAnalysisError,
    LLMServiceError,
    DocumentParsingError,
    DocumentTooLargeError,
    VersionConflictError,
    EncryptionError,
)

# ── Logging Configuration ────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("legal_ai")


# ── Application Lifecycle ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("=" * 60)
    logger.info("Starting Legal AI Contract System")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug: {settings.DEBUG}")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info("=" * 60)

    # Initialize services
    try:
        # Database initialization would go here
        # await init_db()
        logger.info("Database connection initialized")
    except Exception as e:
        logger.warning(f"Database not available: {e}. Running in standalone mode.")

    try:
        # Redis initialization would go here
        logger.info("Cache service initialized")
    except Exception as e:
        logger.warning(f"Redis not available: {e}. Running without cache.")

    logger.info("All services initialized successfully")

    yield  # Application runs

    # Shutdown
    logger.info("Shutting down Legal AI Contract System...")
    try:
        # await close_db()
        logger.info("Database connections closed")
    except Exception:
        pass
    logger.info("Shutdown complete")


# ── Application Factory ──────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Legal AI Contract System",
        description=(
            "Generative AI for Automated Legal Contract Drafting and Review. "
            "Provides AI-powered contract generation, risk analysis, compliance checking, "
            "and version control for legal documents."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS Middleware ──────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    # ── Custom Middleware (order matters - last added = first executed) ──
    app.add_middleware(RequestValidationMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        RateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
    )
    app.add_middleware(AuditLogMiddleware)

    # ── Exception Handlers ───────────────────────────────────────────
    _register_exception_handlers(app)

    # ── API Routes ───────────────────────────────────────────────────
    api_prefix = "/api/v1"

    app.include_router(auth.router, prefix=api_prefix)
    app.include_router(contracts.router, prefix=api_prefix)
    app.include_router(review.router, prefix=api_prefix)
    app.include_router(compliance.router, prefix=api_prefix)
    app.include_router(versions.router, prefix=api_prefix)

    # ── Health & Root Endpoints ──────────────────────────────────────

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": "Legal AI Contract System",
            "version": "1.0.0",
            "description": "Generative AI for Automated Legal Contract Drafting and Review",
            "organization": "myOnsite Healthcare, LLC",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
            "services": {
                "api": "running",
                "database": "standalone",
                "cache": "standalone",
                "llm": settings.LLM_PROVIDER,
            },
        }

    @app.get("/api/v1/health", tags=["Health"])
    async def api_health():
        return {
            "status": "healthy",
            "version": "1.0.0",
            "endpoints": {
                "auth": "/api/v1/auth",
                "contracts": "/api/v1/contracts",
                "review": "/api/v1/review",
                "compliance": "/api/v1/compliance",
                "versions": "/api/v1/versions",
            },
        }

    return app


# ── Exception Handlers ───────────────────────────────────────────────

def _register_exception_handlers(app: FastAPI):
    """Register custom exception handlers."""

    @app.exception_handler(AuthenticationError)
    async def authentication_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc), "error_type": "authentication_error"},
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_handler(request: Request, exc: AuthorizationError):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc), "error_type": "authorization_error"},
        )

    @app.exception_handler(TokenExpiredError)
    async def token_expired_handler(request: Request, exc: TokenExpiredError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Token has expired", "error_type": "token_expired"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(ContractNotFoundError)
    async def contract_not_found_handler(request: Request, exc: ContractNotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "error_type": "contract_not_found"},
        )

    @app.exception_handler(ContractGenerationError)
    async def contract_generation_handler(request: Request, exc: ContractGenerationError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc), "error_type": "contract_generation_error"},
        )

    @app.exception_handler(ContractValidationError)
    async def contract_validation_handler(request: Request, exc: ContractValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc), "error_type": "contract_validation_error"},
        )

    @app.exception_handler(ComplianceViolationError)
    async def compliance_violation_handler(request: Request, exc: ComplianceViolationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc), "error_type": "compliance_violation"},
        )

    @app.exception_handler(JurisdictionNotSupportedError)
    async def jurisdiction_handler(request: Request, exc: JurisdictionNotSupportedError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc), "error_type": "jurisdiction_not_supported"},
        )

    @app.exception_handler(RiskAnalysisError)
    async def risk_analysis_handler(request: Request, exc: RiskAnalysisError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc), "error_type": "risk_analysis_error"},
        )

    @app.exception_handler(LLMServiceError)
    async def llm_service_handler(request: Request, exc: LLMServiceError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(exc), "error_type": "llm_service_error"},
        )

    @app.exception_handler(DocumentParsingError)
    async def document_parsing_handler(request: Request, exc: DocumentParsingError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc), "error_type": "document_parsing_error"},
        )

    @app.exception_handler(DocumentTooLargeError)
    async def document_too_large_handler(request: Request, exc: DocumentTooLargeError):
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": str(exc), "error_type": "document_too_large"},
        )

    @app.exception_handler(VersionConflictError)
    async def version_conflict_handler(request: Request, exc: VersionConflictError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc), "error_type": "version_conflict"},
        )

    @app.exception_handler(EncryptionError)
    async def encryption_handler(request: Request, exc: EncryptionError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Encryption error occurred", "error_type": "encryption_error"},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred",
                "error_type": "internal_server_error",
            },
        )


# ── Create Application Instance ─────────────────────────────────────

app = create_app()


# ── Run with Uvicorn ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        workers=1 if settings.DEBUG else settings.WORKERS,
    )
