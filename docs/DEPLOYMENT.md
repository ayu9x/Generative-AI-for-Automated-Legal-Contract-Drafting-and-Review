# Deployment Guide

## Generative AI for Automated Legal Contract System

---

## Prerequisites

- **Docker** 24.0+ & Docker Compose v2
- **Node.js** 20+ (for local frontend development)
- **Python** 3.11+ (for local backend development)
- **PostgreSQL** 16 (if running without Docker)
- **Redis** 7 (if running without Docker)

---

## Quick Start (Docker)

### 1. Clone & Configure

```bash
cd "Generative AI for Automated Legal Contract"
cp .env.example .env
```

### 2. Edit Environment Variables

Edit `.env` with required values:

```env
# Required
DATABASE_URL=postgresql+asyncpg://legalai:legalai_password@postgres:5432/legalai_db
SECRET_KEY=your-secret-key-min-32-chars
ENCRYPTION_KEY=your-encryption-key-min-32-chars

# LLM Providers (at least one, or use mock)
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=openai  # or: anthropic, mock

# Redis
REDIS_URL=redis://redis:6379/0
```

### 3. Start Services

```bash
docker-compose up -d
```

### 4. Verify

```bash
# Check all containers are running
docker-compose ps

# Test backend health
curl http://localhost:8000/health

# Access frontend
open http://localhost
```

---

## Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start backend (uses mock LLM by default)
python -m app.main
# → http://localhost:8000
# → Swagger docs: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
# → http://localhost:5173
```

### Running Tests

```bash
cd backend
pytest tests/ -v
pytest tests/ -v --tb=short    # Concise output
pytest tests/test_auth.py -v   # Single file
```

---

## Production Deployment

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | — | JWT signing key (32+ chars) |
| `ENCRYPTION_KEY` | Yes | — | AES-256 data encryption key |
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection |
| `OPENAI_API_KEY` | No* | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | No* | — | Anthropic API key |
| `LLM_PROVIDER` | No | `openai` | Primary LLM provider |
| `CORS_ORIGINS` | No | `["*"]` | Allowed CORS origins |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `API_RATE_LIMIT` | No | `100` | Requests per minute |

*At least one LLM provider key required for AI features. Use `LLM_PROVIDER=mock` for testing without keys.

### Security Checklist

- [ ] Set strong, unique `SECRET_KEY` and `ENCRYPTION_KEY`
- [ ] Configure `CORS_ORIGINS` to specific domains (not `*`)
- [ ] Enable HTTPS via reverse proxy (Nginx/Cloudflare)
- [ ] Set `LOG_LEVEL=WARNING` in production
- [ ] Use strong PostgreSQL password
- [ ] Disable Elasticsearch security bypass for production
- [ ] Configure rate limiting appropriately
- [ ] Set up database backups
- [ ] Review and restrict Docker network access
- [ ] Enable MFA for admin accounts

### Scaling

**Horizontal:**
```yaml
# docker-compose.override.yml
services:
  backend:
    deploy:
      replicas: 3
```

**Backend workers:**
```env
# .env
WORKERS=4  # Default: CPU cores * 2 + 1
```

**Database pooling:**
```env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

---

## Service Ports

| Service | Internal Port | External Port |
|---------|--------------|---------------|
| Backend (FastAPI) | 8000 | 8000 |
| Frontend (Nginx) | 80 | 80 |
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |
| Elasticsearch | 9200 | 9200 |

---

## Monitoring & Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend

# Health check
curl http://localhost:8000/health
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend won't start | Check `DATABASE_URL` format, ensure PostgreSQL is running |
| LLM errors | Verify API keys, or set `LLM_PROVIDER=mock` |
| Frontend can't reach API | Check Nginx config, ensure backend is on port 8000 |
| Rate limit errors | Increase `API_RATE_LIMIT` or whitelist IPs |
| Database connection errors | Check PostgreSQL container health, verify credentials |
| Redis connection refused | Ensure Redis container is running and healthy |
