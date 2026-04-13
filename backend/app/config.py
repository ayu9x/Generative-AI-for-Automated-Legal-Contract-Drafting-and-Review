"""Configuration management for Legal Contract AI System."""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    APP_NAME: str = "Legal Contract AI System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    API_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/legal_contracts.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # Security
    SECRET_KEY: str = Field(default="change-this-in-production-to-a-secure-random-key-minimum-32-chars")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENCRYPTION_KEY: str = Field(default="change-this-32-byte-key-in-prod!")
    BCRYPT_ROUNDS: int = 12

    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "groq"
    LLM_PROVIDER: str = "groq"  # Alias for DEFAULT_LLM_PROVIDER
    DEFAULT_LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_MAX_TOKENS: int = 8192
    LLM_TEMPERATURE: float = 0.1
    LLM_REQUEST_TIMEOUT: int = 120

    # Web Search
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_SEARCH_CX: Optional[str] = None
    WEB_SEARCH_ENABLED: bool = True
    WEB_SEARCH_MAX_RESULTS: int = 5

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX_PREFIX: str = "legal_"

    # Vector Database
    VECTOR_DB_PROVIDER: str = "chromadb"
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    CHROMADB_PERSIST_DIR: str = "./data/chromadb"

    # Document Processing
    MAX_DOCUMENT_SIZE_MB: int = 50
    SUPPORTED_FORMATS: List[str] = ["pdf", "docx", "txt", "md"]
    MAX_PAGES_PER_DOCUMENT: int = 500

    # Compliance
    DEFAULT_JURISDICTION: str = "US-Federal"
    SUPPORTED_JURISDICTIONS: List[str] = [
        "US-Federal", "US-CA", "US-NY", "US-TX", "US-FL", "US-IL",
        "US-DE", "US-WA", "US-MA", "US-GA", "US-PA",
        "UK", "EU-GDPR", "EU-DE", "EU-FR", "EU-ES",
        "CA-Federal", "CA-ON", "CA-BC", "CA-QC",
        "AU", "SG", "HK", "JP", "IN", "BR", "MX",
        "UAE", "SA", "ZA", "NG", "KE",
        "CH", "SE", "NO", "DK", "FI",
        "NL", "BE", "IT", "AT", "IE",
        "NZ", "PH", "MY", "TH", "KR",
        "IL", "TR", "PL", "CZ", "RO"
    ]

    # Risk Analysis
    RISK_FACTORS_COUNT: int = 500
    RISK_SCORE_THRESHOLD_HIGH: float = 0.7
    RISK_SCORE_THRESHOLD_MEDIUM: float = 0.4
    RISK_SCORE_THRESHOLD_LOW: float = 0.2

    # Performance
    CONTRACT_GENERATION_TIMEOUT: int = 30
    REVIEW_TIMEOUT: int = 120
    MAX_CONCURRENT_REQUESTS: int = 10000
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    RATE_LIMIT_PER_MINUTE: int = 100

    # Audit
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 2555  # ~7 years for legal compliance

    # File Storage
    STORAGE_BACKEND: str = "local"  # local, s3, azure
    STORAGE_PATH: str = "./data/documents"
    S3_BUCKET: Optional[str] = None
    S3_REGION: Optional[str] = None

    class Config:
        # Look for .env in current dir first, then parent (project root)
        import os as _os
        _env_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", ".env")
        env_file = _env_path if _os.path.isfile(_env_path) else ".env"
        case_sensitive = True


settings = Settings()
