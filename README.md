<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.104+-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-18.2-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/TypeScript-5.2-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
  <img src="https://img.shields.io/badge/Vite-5.0-646CFF?style=for-the-badge&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

# ⚖️ Generative AI for Automated Legal Contract Drafting & Review

> An enterprise-grade AI platform for autonomous legal contract drafting, risk analysis, compliance verification, and version control — powered by GPT-4 and Claude.

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Default Credentials](#-default-credentials)
- [API Documentation](#-api-documentation)
- [API Endpoints](#-api-endpoints)
- [Frontend Pages](#-frontend-pages)
- [Configuration](#%EF%B8%8F-configuration)
- [Docker Deployment](#-docker-deployment)
- [Performance Targets](#-performance-targets)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

This system provides a production-ready platform for legal teams to:

- **Draft** customized contracts from natural language instructions using AI
- **Review** existing contracts for hidden risks with explainable scoring
- **Verify** compliance against 50+ jurisdictions and regulations (GDPR, HIPAA, SOX, etc.)
- **Track** document revisions with Git-like version control and redlining

The backend runs in **standalone demo mode** by default — no database or Redis required. Just install, run, and start drafting contracts.

---

## 🚀 Key Features

### 🤖 Contract Generation Engine
| Capability | Details |
|---|---|
| Natural Language → Contract | Describe what you need in plain English |
| Template Library | 200+ templates (NDA, MSA, Employment, M&A, SaaS, Licensing, etc.) |
| Multi-Jurisdiction | 50+ jurisdictions with region-specific clauses |
| Multi-Language | 15+ language support |
| AI Clause Suggestions | Context-aware recommendations from GPT-4 / Claude |

### 🔍 Risk Analysis & Review
- **500+ risk factors** analyzed per contract with explainable AI
- Clause-by-clause risk scoring (Critical / High / Medium / Low)
- Anomaly detection for unusual or missing provisions
- Precedent-based comparison against industry standards
- AI-generated remediation suggestions

### ✅ Compliance Checking
- Real-time regulatory compliance verification
- Supports **GDPR, HIPAA, SOX, CCPA, PCI-DSS, and 50,000+ regulatory rules**
- Cross-jurisdictional conflict detection and resolution
- Automated compliance reports with citation references

### 📝 Version Control & Collaboration
- Git-like branching, merging, and version history for legal documents
- Visual diff / redlining with inline change tracking
- Multi-party negotiation workflows
- Role-based access control (ADMIN, LEGAL_ADMIN, SENIOR_ATTORNEY, CONTRACT_VIEWER)

### 🔐 Enterprise Security
- AES-256 (Fernet) encryption for sensitive contract data
- JWT authentication with refresh tokens
- Rate limiting, request validation, and security headers
- Complete audit trail logging for every action
- API key generation for programmatic access

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Frontend (React + TypeScript + Vite)         │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐   │
│  │ Contract  │ │   Risk    │ │Compliance │ │   Version     │   │
│  │ Generator │ │ Analysis  │ │  Center   │ │   History     │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────────┘   │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐                     │
│  │ Dashboard │ │  Login    │ │ Contract  │                     │
│  │           │ │           │ │   View    │                     │
│  └───────────┘ └───────────┘ └───────────┘                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │  REST API (Axios)
┌──────────────────────────┴──────────────────────────────────────┐
│                     API Gateway (FastAPI)                        │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐   │
│  │   Auth    │ │  Audit    │ │   Rate    │ │  Security     │   │
│  │Middleware │ │  Logger   │ │  Limiter  │ │  Headers      │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                     Core Services                                │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Contract         │  │ Risk Analyzer    │                     │
│  │ Generator        │  │ (500+ factors)   │                     │
│  └──────────────────┘  └──────────────────┘                     │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ Compliance       │  │ Version Control  │                     │
│  │ Checker (50+)    │  │ (Git-like)       │                     │
│  └──────────────────┘  └──────────────────┘                     │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ LLM Service      │  │ Template Engine  │                     │
│  │ (GPT-4 / Claude) │  │ (200+ types)     │                     │
│  └──────────────────┘  └──────────────────┘                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                     Data Layer (Optional for Demo)               │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐   │
│  │PostgreSQL │ │   Redis   │ │ Elastic-  │ │ ChromaDB /    │   │
│  │(Contracts)│ │  (Cache)  │ │  search   │ │  Pinecone     │   │
│  └───────────┘ └───────────┘ └───────────┘ └───────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, TypeScript 5, Vite 5, TailwindCSS 3 |
| **State Management** | Zustand, TanStack React Query |
| **UI Components** | Lucide React (icons), React Hot Toast (notifications) |
| **Routing** | React Router DOM v6 |
| **Backend** | FastAPI, Uvicorn, Python 3.11+ |
| **Authentication** | JWT (python-jose), bcrypt (passlib) |
| **Encryption** | AES-256 via Fernet (cryptography) |
| **AI / LLM** | OpenAI GPT-4, Anthropic Claude, tiktoken |
| **Database** | PostgreSQL + SQLAlchemy + Alembic (optional for demo) |
| **Cache** | Redis (optional for demo) |
| **Search** | Elasticsearch (optional) |
| **Vector DB** | ChromaDB / Pinecone (optional) |
| **Document Processing** | python-docx, PyPDF2, Jinja2, Markdown |
| **Monitoring** | structlog, prometheus-client |
| **Containerization** | Docker, Docker Compose, Nginx |

---

## 📁 Project Structure

```
📦 Generative AI for Automated Legal Contract
├── 📂 backend/
│   ├── 📂 app/
│   │   ├── main.py                        # FastAPI application entry point
│   │   ├── config.py                      # Pydantic settings with env var support
│   │   ├── 📂 api/
│   │   │   ├── 📂 routes/
│   │   │   │   ├── auth.py                # Login, register, JWT tokens, API keys
│   │   │   │   ├── contracts.py           # CRUD operations for contracts
│   │   │   │   ├── review.py              # AI-powered contract review
│   │   │   │   ├── compliance.py          # Regulatory compliance checking
│   │   │   │   └── versions.py            # Document version control
│   │   │   └── 📂 middleware/
│   │   │       ├── security.py            # Rate limiting, headers, validation
│   │   │       └── audit.py               # Request/response audit logging
│   │   ├── 📂 core/
│   │   │   ├── security.py                # JWT, bcrypt, AES-256 encryption
│   │   │   ├── database.py                # SQLAlchemy async engine setup
│   │   │   └── exceptions.py              # Custom exception hierarchy
│   │   ├── 📂 models/
│   │   │   ├── contract.py                # Contract data models
│   │   │   ├── user.py                    # User & role models
│   │   │   ├── risk.py                    # Risk assessment models
│   │   │   ├── compliance.py              # Compliance result models
│   │   │   ├── version.py                 # Version control models
│   │   │   └── audit.py                   # Audit log models
│   │   ├── 📂 services/
│   │   │   ├── contract_generator.py      # AI contract drafting logic
│   │   │   ├── risk_analyzer.py           # 500+ factor risk analysis
│   │   │   ├── compliance_checker.py      # Multi-jurisdiction compliance
│   │   │   ├── llm_service.py             # GPT-4 / Claude integration
│   │   │   ├── template_engine.py         # 200+ contract templates
│   │   │   └── version_control.py         # Git-like document versioning
│   │   └── 📂 utils/                      # Shared utilities
│   ├── 📂 tests/                          # Pytest test suites
│   └── requirements.txt
├── 📂 frontend/
│   ├── 📂 src/
│   │   ├── App.tsx                        # Root component with routing
│   │   ├── main.tsx                       # React entry point
│   │   ├── index.css                      # Global styles (Tailwind)
│   │   ├── 📂 pages/
│   │   │   ├── Login.tsx                  # Authentication page
│   │   │   ├── Dashboard.tsx              # Overview & statistics
│   │   │   ├── ContractGenerator.tsx      # AI contract creation
│   │   │   ├── ContractView.tsx           # Contract detail view
│   │   │   ├── RiskAnalysis.tsx           # Risk scoring dashboard
│   │   │   ├── ComplianceCenter.tsx       # Compliance verification
│   │   │   └── VersionHistory.tsx         # Document version timeline
│   │   ├── 📂 services/
│   │   │   └── api.ts                     # Axios API client
│   │   ├── 📂 store/
│   │   │   └── authStore.ts               # Zustand auth state
│   │   └── 📂 components/                 # Reusable UI components
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
├── 📂 docs/
│   ├── API_DOCUMENTATION.md               # Full API reference
│   ├── ARCHITECTURE.md                    # System design deep-dive
│   └── DEPLOYMENT.md                      # Production deployment guide
├── .env.example                           # Environment variable template
├── docker-compose.yml                     # Full-stack Docker setup
├── Dockerfile.backend                     # Backend container
├── Dockerfile.frontend                    # Frontend container
├── nginx.conf                             # Reverse proxy configuration
└── README.md
```

---

## 🏁 Getting Started

### Prerequisites

| Requirement | Version | Required? |
|---|---|---|
| Python | 3.11+ | ✅ Yes |
| Node.js | 18+ | ✅ Yes |
| npm | 9+ | ✅ Yes |
| PostgreSQL | 15+ | ❌ Optional (demo uses in-memory) |
| Redis | 7+ | ❌ Optional (demo runs without cache) |
| Docker | 24+ | ❌ Optional (for containerized deployment) |

### Option 1: Manual Setup (Recommended for Development)

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd "Generative AI for Automated Legal Contract"
```

#### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys (optional — app uses mock LLM by default)
```

#### 3. Start the Backend

```bash
# Create virtual environment
cd backend
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# ⚠️ Important: Pin bcrypt for passlib compatibility
pip install bcrypt==4.0.1

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 4. Start the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

#### 5. Open in Browser

| Service | URL |
|---|---|
| Frontend App | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

### Option 2: Docker Compose

```bash
docker-compose up -d
```

This spins up the backend, frontend, PostgreSQL, Redis, and Nginx reverse proxy.

---

## 🔑 Default Credentials

A demo admin account is seeded automatically on startup:

| Field | Value |
|---|---|
| **Email** | `admin@legalai.com` |
| **Password** | `Admin@123456` |
| **Role** | `ADMIN` |

> **Note:** You can also register new users via the `/api/v1/auth/register` endpoint or the Login page.

---

## 📡 API Documentation

Interactive API docs are available when the backend is running:

- **Swagger UI** — http://localhost:8000/docs
- **ReDoc** — http://localhost:8000/redoc
- **OpenAPI JSON** — http://localhost:8000/openapi.json

See [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) for the full offline reference.

---

## 🔌 API Endpoints

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new user |
| `POST` | `/auth/login` | Login and receive JWT tokens |
| `POST` | `/auth/refresh` | Refresh access token |
| `GET` | `/auth/me` | Get current user profile |
| `PUT` | `/auth/me` | Update profile |
| `POST` | `/auth/change-password` | Change password |
| `POST` | `/auth/api-key` | Generate API key |
| `POST` | `/auth/logout` | Logout |

### Contracts (`/api/v1/contracts`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/contracts/generate` | Generate a contract using AI |
| `GET` | `/contracts/` | List all contracts |
| `GET` | `/contracts/{id}` | Get contract details |
| `PUT` | `/contracts/{id}` | Update a contract |
| `DELETE` | `/contracts/{id}` | Delete a contract (Admin only) |

### Review (`/api/v1/review`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/review/analyze` | Analyze and review a contract |
| `POST` | `/review/compare` | Compare two contract versions |
| `POST` | `/review/suggest` | Get AI improvement suggestions |

### Compliance (`/api/v1/compliance`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/compliance/check` | Run compliance check against frameworks |
| `GET` | `/compliance/jurisdictions` | List supported jurisdictions |
| `GET` | `/compliance/frameworks` | List supported compliance frameworks |
| `POST` | `/compliance/report` | Generate compliance report |

### Versions (`/api/v1/versions`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/versions/{contract_id}` | Get version history |
| `POST` | `/versions/{contract_id}` | Create a new version |
| `GET` | `/versions/{contract_id}/{version}` | Get specific version |
| `POST` | `/versions/compare` | Compare two versions |
| `POST` | `/versions/merge` | Merge versions (Admin/Sr. Attorney) |
| `POST` | `/versions/branch` | Create a branch |

---

## 🖥 Frontend Pages

| Page | Route | Description |
|---|---|---|
| **Login** | `/login` | User authentication |
| **Dashboard** | `/dashboard` | Overview, stats, recent contracts |
| **Contract Generator** | `/generator` | AI-powered contract creation wizard |
| **Contract View** | `/contracts/:id` | Full contract with metadata |
| **Risk Analysis** | `/risk-analysis` | Risk scoring & breakdown |
| **Compliance Center** | `/compliance` | Compliance check workflows |
| **Version History** | `/versions` | Document revision timeline & diffs |

---

## ⚙️ Configuration

All configuration is managed via environment variables (`.env` file). Key settings:

```bash
# ── Application ──────────────────────────────
ENVIRONMENT=development        # development | staging | production
DEBUG=true                     # Enable hot-reload and verbose logging

# ── Security ─────────────────────────────────
SECRET_KEY=your-secret-key     # JWT signing key (min 32 chars)
ENCRYPTION_KEY=your-enc-key    # AES-256 encryption key (32 bytes)

# ── LLM (leave empty for mock/demo mode) ─────
OPENAI_API_KEY=                # Your OpenAI API key for GPT-4
ANTHROPIC_API_KEY=             # Your Anthropic API key for Claude
DEFAULT_LLM_PROVIDER=openai   # openai | anthropic
DEFAULT_LLM_MODEL=gpt-4       # gpt-4 | gpt-3.5-turbo | claude-3

# ── Database (optional for demo) ─────────────
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/legal_contracts

# ── Redis (optional for demo) ────────────────
REDIS_URL=redis://localhost:6379/0

# ── CORS ─────────────────────────────────────
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:8000"]
```

> **Tip:** The app runs fully without PostgreSQL, Redis, or LLM API keys. It uses in-memory stores and a mock LLM provider by default — perfect for development and demos.

---

## 🐳 Docker Deployment

```bash
# Build and start all services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down
```

The Docker setup includes:
- Backend API container
- Frontend Nginx container
- PostgreSQL database
- Redis cache
- Nginx reverse proxy

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for production deployment instructions.

---

## 📊 Performance Targets

| Metric | Target |
|---|---|
| Contract Generation | < 30 seconds |
| Document Review (100 pages) | < 2 minutes |
| Concurrent Users | 10,000+ |
| Monthly Throughput | 1M+ contracts |
| System Availability | 99.99% |
| Legal Accuracy | > 99.9% |
| API Response (p95) | < 200ms |
| Rate Limit | 100 requests/min/user |

---

## 📚 Documentation

| Document | Description |
|---|---|
| [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) | Complete API reference with request/response examples |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design, data flow, and component interactions |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Production deployment, scaling, and infrastructure guide |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## ⚠️ Known Issues

- **bcrypt compatibility**: `passlib` is incompatible with `bcrypt>=4.1`. Pin to `bcrypt==4.0.1` to avoid startup errors.
- **LLM responses**: Without valid API keys, the system uses a mock LLM provider that returns template-based responses.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ using FastAPI + React + Generative AI
</p>
