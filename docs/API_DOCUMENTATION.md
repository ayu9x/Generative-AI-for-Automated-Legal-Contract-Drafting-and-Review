# API Documentation

## Generative AI for Automated Legal Contract System

**Base URL:** `http://localhost:8000/api/v1`  
**Authentication:** Bearer JWT Token  
**Content-Type:** `application/json`

---

## Authentication

### POST `/auth/register`
Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "role": "attorney"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "attorney",
  "created_at": "2025-08-01T00:00:00Z"
}
```

### POST `/auth/login`
Authenticate and receive tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "attorney"
  }
}
```

### POST `/auth/refresh`
Refresh an expired access token.

**Headers:** `Authorization: Bearer <refresh_token>`

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### GET `/auth/me`
Get current user profile.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "attorney"
}
```

### POST `/auth/change-password`
Change the current user's password.

**Request:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

### POST `/auth/api-key`
Generate a new API key for programmatic access.

**Response (200):**
```json
{
  "api_key": "lc_abc123...",
  "created_at": "2025-08-01T00:00:00Z"
}
```

### POST `/auth/logout`
Invalidate the current session.

---

## Contracts

### GET `/contracts/templates`
List all available contract templates.

**Response (200):**
```json
{
  "templates": [
    {
      "type": "nda",
      "name": "Non-Disclosure Agreement",
      "description": "Standard NDA template...",
      "complexity": "low",
      "required_variables": ["disclosing_party", "receiving_party", "effective_date", "duration", "governing_law"]
    }
  ]
}
```

### POST `/contracts/generate`
Generate a new contract using AI.

**Request:**
```json
{
  "contract_type": "nda",
  "title": "Mutual NDA for Project X",
  "jurisdiction": "US-CA",
  "parties": [
    {
      "name": "Acme Corp",
      "role": "disclosing_party",
      "address": "123 Main St, San Francisco, CA",
      "contact_email": "legal@acme.com"
    },
    {
      "name": "Beta Inc",
      "role": "receiving_party",
      "address": "456 Oak Ave, Los Angeles, CA",
      "contact_email": "legal@beta.com"
    }
  ],
  "variables": {
    "effective_date": "2025-08-01",
    "duration": "2 years",
    "governing_law": "California"
  },
  "special_requirements": "Include carve-outs for publicly available information",
  "ai_enhanced": true
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "title": "Mutual NDA for Project X",
  "contract_type": "nda",
  "content": "MUTUAL NON-DISCLOSURE AGREEMENT...",
  "status": "draft",
  "jurisdiction": "US-CA",
  "parties": [...],
  "metadata": {
    "word_count": 2500,
    "clause_count": 12,
    "ai_model": "gpt-4",
    "content_hash": "sha256..."
  },
  "clauses": [
    {
      "title": "Definition of Confidential Information",
      "content": "...",
      "position": 1
    }
  ],
  "created_at": "2025-08-01T00:00:00Z"
}
```

### GET `/contracts/`
List contracts with pagination and filtering.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `skip` | int | 0 | Offset |
| `limit` | int | 20 | Page size (max 100) |
| `status` | string | — | Filter by status |
| `contract_type` | string | — | Filter by type |

**Response (200):**
```json
{
  "contracts": [...],
  "total": 42,
  "skip": 0,
  "limit": 20
}
```

### GET `/contracts/{contract_id}`
Get a specific contract by ID.

### PUT `/contracts/{contract_id}`
Update a contract.

**Request:**
```json
{
  "title": "Updated Title",
  "content": "Updated content...",
  "status": "under_review"
}
```

### DELETE `/contracts/{contract_id}`
Delete a contract (admin only).

### POST `/contracts/{contract_id}/summary`
Generate an AI summary of a contract.

**Response (200):**
```json
{
  "contract_id": "uuid",
  "summary": "This NDA establishes mutual confidentiality obligations between..."
}
```

### POST `/contracts/explain-clause`
Get an AI explanation of a specific clause.

**Request:**
```json
{
  "clause_text": "The Receiving Party shall not disclose...",
  "context": "NDA between technology companies"
}
```

**Response (200):**
```json
{
  "clause_text": "...",
  "explanation": "This clause establishes the core obligation...",
  "legal_implications": [
    "Creates a binding duty of confidentiality",
    "Applies to the Receiving Party specifically"
  ],
  "risk_factors": [
    "Broad definition may be difficult to enforce"
  ]
}
```

### POST `/contracts/upload`
Upload an existing contract document for analysis.

**Content-Type:** `multipart/form-data`  
**Field:** `file` (PDF, DOCX, TXT)

### GET `/contracts/{contract_id}/export`
Export contract in specified format.

**Query Parameters:**
| Param | Type | Default | Options |
|-------|------|---------|---------|
| `format` | string | `docx` | `docx`, `pdf`, `txt`, `html`, `markdown` |

---

## Review & Risk Analysis

### POST `/review/risk-analysis`
Perform risk analysis on contract content.

**Request:**
```json
{
  "contract_id": "uuid",
  "content": "AGREEMENT... full contract text...",
  "contract_type": "nda",
  "jurisdiction": "US-CA",
  "categories": ["financial", "regulatory", "data_privacy"]
}
```

**Response (200):**
```json
{
  "id": "uuid",
  "contract_id": "uuid",
  "overall_score": 72.5,
  "risk_level": "medium",
  "categories": {
    "financial": {
      "score": 65.0,
      "level": "medium",
      "factors": [
        {
          "name": "Unlimited Liability",
          "severity": "high",
          "description": "Contract contains unlimited liability exposure",
          "recommendation": "Add a liability cap provision"
        }
      ]
    }
  },
  "executive_summary": "The contract presents moderate risk overall...",
  "recommendations": [
    "Add liability cap provisions",
    "Include data breach notification requirements"
  ]
}
```

### POST `/review/batch-analysis`
Analyze multiple contracts (admin/senior attorney only).

**Request:**
```json
{
  "analyses": [
    { "contract_id": "uuid1", "content": "..." },
    { "contract_id": "uuid2", "content": "..." }
  ]
}
```

### GET `/review/analysis/{analysis_id}`
Retrieve a previous risk analysis.

### GET `/review/history/{contract_id}`
Get all risk analyses for a contract.

### POST `/review/comments`
Add a review comment.

**Request:**
```json
{
  "contract_id": "uuid",
  "content": "Section 3.2 needs revision for compliance",
  "section": "Section 3.2",
  "comment_type": "revision_required"
}
```

### GET `/review/comments/{contract_id}`
Get all comments for a contract.

### PUT `/review/comments/{comment_id}/resolve`
Resolve a review comment.

### GET `/review/status/{contract_id}`
Get overall review status.

---

## Compliance

### POST `/compliance/check`
Run compliance check against selected frameworks.

**Request:**
```json
{
  "contract_id": "uuid",
  "content": "AGREEMENT... full contract text...",
  "jurisdiction": "US-CA",
  "frameworks": ["gdpr", "hipaa", "ccpa"],
  "contract_type": "service_agreement"
}
```

**Response (200):**
```json
{
  "id": "uuid",
  "contract_id": "uuid",
  "overall_score": 85.0,
  "status": "compliant_with_warnings",
  "frameworks_checked": ["gdpr", "hipaa", "ccpa"],
  "results": [
    {
      "rule_id": "gdpr_001",
      "framework": "gdpr",
      "rule_name": "Data Processing Agreement Required",
      "status": "compliant",
      "details": "Contract includes data processing provisions",
      "severity": "critical"
    },
    {
      "rule_id": "hipaa_001",
      "framework": "hipaa",
      "rule_name": "BAA Required",
      "status": "non_compliant",
      "details": "Missing Business Associate Agreement",
      "severity": "critical",
      "recommendation": "Add BAA provisions per 45 CFR 164.502(e)"
    }
  ],
  "framework_scores": {
    "gdpr": 90.0,
    "hipaa": 70.0,
    "ccpa": 95.0
  },
  "recommendations": [
    "Add Business Associate Agreement provisions for HIPAA compliance"
  ]
}
```

### GET `/compliance/check/{check_id}`
Retrieve a previous compliance check.

### GET `/compliance/history/{contract_id}`
Get compliance check history for a contract.

### GET `/compliance/jurisdictions`
List supported jurisdictions.

**Response (200):**
```json
{
  "jurisdictions": [
    {
      "code": "US-CA",
      "name": "California, United States",
      "legal_system": "common_law",
      "frameworks": ["ccpa", "general_contract_law"]
    }
  ]
}
```

### GET `/compliance/jurisdictions/{code}`
Get details for a specific jurisdiction.

### GET `/compliance/frameworks`
List all compliance frameworks with rule counts.

### POST `/compliance/report`
Generate a comprehensive compliance report.

### GET `/compliance/updates`
Get recent regulatory updates.

---

## Version Control

### POST `/versions/`
Create a new version of a contract.

**Request:**
```json
{
  "contract_id": "uuid",
  "content": "Updated contract content...",
  "change_description": "Added force majeure clause",
  "branch": "main"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "contract_id": "uuid",
  "version_number": 2,
  "content": "...",
  "change_description": "Added force majeure clause",
  "content_hash": "sha256...",
  "branch": "main",
  "created_by": "user-uuid",
  "created_at": "2025-08-01T00:00:00Z"
}
```

### GET `/versions/{contract_id}`
Get version history for a contract.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `branch` | string | `main` | Branch name |

### GET `/versions/{contract_id}/version/{version_id}`
Get a specific version.

### POST `/versions/diff`
Compare two versions.

**Request:**
```json
{
  "contract_id": "uuid",
  "version_id_1": "uuid",
  "version_id_2": "uuid"
}
```

**Response (200):**
```json
{
  "contract_id": "uuid",
  "version_1": 1,
  "version_2": 2,
  "changes": {
    "additions": 5,
    "deletions": 2,
    "modifications": 3
  },
  "diff_text": "...",
  "redline_html": "<div class='redline'>..."
}
```

### POST `/versions/branches`
Create a new branch.

**Request:**
```json
{
  "contract_id": "uuid",
  "branch_name": "legal-review",
  "source_branch": "main",
  "description": "Branch for legal team review"
}
```

### GET `/versions/{contract_id}/branches`
List branches for a contract.

### POST `/versions/merge`
Merge a branch into target.

**Request:**
```json
{
  "contract_id": "uuid",
  "source_branch": "legal-review",
  "target_branch": "main"
}
```

### POST `/versions/approve`
Approve a specific version.

### POST `/versions/restore`
Restore contract to a previous version.

### POST `/versions/comments`
Add a comment to a version.

### GET `/versions/comments/{version_id}`
Get comments on a version.

### PUT `/versions/comments/{comment_id}/resolve`
Resolve a version comment.

---

## Health & Status

### GET `/`
Root health check.

### GET `/health`
Detailed health check.

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-08-01T00:00:00Z"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error description",
  "error_code": "ERROR_TYPE",
  "timestamp": "2025-08-01T00:00:00Z"
}
```

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request / Validation Error |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource Not Found |
| 409 | Conflict (e.g., duplicate, version conflict) |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |

## Rate Limits

- **Default:** 100 requests per minute per IP
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
