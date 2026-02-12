# Architecture Documentation

## Generative AI for Automated Legal Contract Drafting and Review

**Version:** 1.0.0  
**Version:** 1.0.0  
**Date:** August 2025

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │Dashboard │ │Generator │ │Risk View │ │Compliance│          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐                                      │
│  │VersionUI │ │  Login   │   State: Zustand | API: Axios        │
│  └──────────┘ └──────────┘   Styling: Tailwind CSS              │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP/REST (JSON)
┌──────────────────────▼──────────────────────────────────────────┐
│                    API GATEWAY (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Middleware: Rate Limit │ Security Headers │ Audit Log    │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌──────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ ┌────────┐     │
│  │ Auth │ │Contracts │ │ Review │ │Compliance│ │Version │     │
│  │Routes│ │  Routes  │ │ Routes │ │  Routes  │ │ Routes │     │
│  └──────┘ └──────────┘ └────────┘ └──────────┘ └────────┘     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                     SERVICE LAYER                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐        │
│  │  Contract    │ │    Risk      │ │   Compliance     │        │
│  │  Generator   │ │   Analyzer   │ │    Checker       │        │
│  └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘        │
│         │                │                   │                   │
│  ┌──────▼───────┐ ┌──────▼───────┐ ┌────────▼─────────┐        │
│  │   Template   │ │  LLM Service │ │  Version Control │        │
│  │   Engine     │ │  (Multi-     │ │   Service        │        │
│  │  (Jinja2)    │ │   Provider)  │ │  (Git-Like)      │        │
│  └──────────────┘ └──────────────┘ └──────────────────┘        │
│  ┌──────────────┐ ┌──────────────┐                              │
│  │  Document    │ │   Security   │                              │
│  │  Processor   │ │   (AES-256)  │                              │
│  └──────────────┘ └──────────────┘                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                    DATA LAYER                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────┐      │
│  │PostgreSQL│ │  Redis   │ │Elasticsearch │ │ ChromaDB │      │
│  │ (Primary)│ │ (Cache)  │ │  (Search)    │ │ (Vector) │      │
│  └──────────┘ └──────────┘ └──────────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Frontend (React + TypeScript)

| Component | File | Purpose |
|-----------|------|---------|
| App | `src/App.tsx` | Route definitions, auth guard |
| Layout | `src/components/Layout.tsx` | Sidebar navigation, user menu |
| Login | `src/pages/Login.tsx` | Authentication (login/register) |
| Dashboard | `src/pages/Dashboard.tsx` | Overview stats, recent contracts |
| ContractGenerator | `src/pages/ContractGenerator.tsx` | AI contract creation wizard |
| ContractView | `src/pages/ContractView.tsx` | View, edit, analyze contracts |
| RiskAnalysis | `src/pages/RiskAnalysis.tsx` | Risk scoring and factor display |
| ComplianceCenter | `src/pages/ComplianceCenter.tsx` | Multi-framework compliance checks |
| VersionHistory | `src/pages/VersionHistory.tsx` | Git-like version timeline |

**State Management:** Zustand with localStorage persistence  
**API Client:** Axios with JWT interceptors  
**Styling:** Tailwind CSS  
**Build Tool:** Vite

### 2. Backend API (FastAPI)

#### API Routes (`/api/v1/`)

| Prefix | Module | Endpoints |
|--------|--------|-----------|
| `/auth` | `auth.py` | Register, Login, Refresh, Profile, Change Password, API Keys |
| `/contracts` | `contracts.py` | CRUD, Generate, Upload, Export, Summarize, Explain Clause |
| `/review` | `review.py` | Risk Analysis, Batch Analysis, Comments, Review Status |
| `/compliance` | `compliance.py` | Check, Report, Jurisdictions, Frameworks, Regulatory Updates |
| `/versions` | `versions.py` | Create, History, Diff, Branch, Merge, Approve, Comments |

#### Middleware Stack

1. **AuditLogMiddleware** — Logs all API requests with user, action, duration
2. **RateLimitMiddleware** — Sliding window rate limiting (configurable per minute)
3. **SecurityHeadersMiddleware** — CSP, HSTS, X-Frame-Options, etc.
4. **RequestValidationMiddleware** — Content length, content type validation
5. **CORSMiddleware** — Cross-origin request handling

### 3. Service Layer

#### Contract Generator
- Template-based generation using Jinja2 (8 contract types)
- LLM enhancement for comprehensive language
- Post-processing: clause extraction, validation, hashing
- Supports: NDA, MSA, Employment, Service, License, Partnership, M&A, Lease

#### Risk Analyzer
- 35+ rule-based risk factors across 11 categories
- Categories: financial, regulatory, operational, legal_liability, IP, data_privacy, termination, confidentiality, dispute_resolution, force_majeure, non_compete
- Keyword detection + absence risk analysis
- LLM-enhanced analysis with confidence scoring
- Executive summary generation

#### Compliance Checker
- 25+ compliance rules across 8 frameworks
- Frameworks: GDPR, HIPAA, SOX, CCPA, Employment, General Contract Law, International Trade, Anti-Corruption
- Rule types: mandatory_inclusion, prohibited, conditional
- Multi-jurisdiction support (50+ jurisdictions configurable)

#### Version Control Service
- Git-like version management with branching/merging
- Content-hash based change detection (SHA-256)
- Diff computation using Python difflib
- Redline HTML generation (additions, deletions, modifications)
- Threaded comments with resolution workflow
- Approval workflow with role-based permissions

#### LLM Service (Multi-Provider)
- **OpenAI** — GPT-4 with retry logic, streaming support
- **Anthropic** — Claude Sonnet with fallback embeddings
- **Mock** — Development/testing provider with realistic output
- Provider chain fallback (primary → secondary → mock)
- Domain-specific prompts for legal context

### 4. Security Architecture

| Feature | Implementation |
|---------|---------------|
| Authentication | JWT (HS256) with access + refresh tokens |
| Password Hashing | bcrypt with 12 rounds |
| Data Encryption | AES-256 via Fernet (PBKDF2 key derivation) |
| Document Integrity | SHA-256 content hashing |
| API Keys | Secure random generation (secrets module) |
| Data Masking | PII detection and masking for logs |
| RBAC | 8 roles: Admin, Legal Admin, Senior Attorney, Attorney, Paralegal, Contract Manager, Auditor, Viewer |

### 5. Data Models

- **User** — Authentication, roles, MFA, sessions
- **Contract** — 18 types, 9 statuses, AI metadata, content hash
- **ContractClause** — Individual clause tracking
- **RiskAssessment** — Scores, factors, explanations
- **ComplianceCheck** — Rule results, framework scores
- **ContractVersion** — Git-like versioning with branches
- **AuditLog** — 25+ action types for full audit trail
- **Jurisdiction** — Legal systems, mandatory/prohibited clauses

---

## Deployment

### Docker Compose Stack

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| backend | Custom (Python 3.11) | 8000 | FastAPI application |
| frontend | Custom (Nginx) | 80 | React SPA + reverse proxy |
| postgres | PostgreSQL 16 | 5432 | Primary database |
| redis | Redis 7 | 6379 | Caching & sessions |
| elasticsearch | ES 8.11 | 9200 | Full-text search |

### Quick Start

```bash
# Clone and configure
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# Or run backend locally
cd backend
pip install -r requirements.txt
python -m app.main

# Run frontend locally
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Contract Generation | < 30 seconds |
| Risk Analysis | < 15 seconds |
| Compliance Check | < 10 seconds |
| API Response (P95) | < 500ms |
| Concurrent Users | 100+ |
| Contract Accuracy | 99.9% |
| System Uptime | 99.95% |

---

## API Documentation

Once running, access interactive docs at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
