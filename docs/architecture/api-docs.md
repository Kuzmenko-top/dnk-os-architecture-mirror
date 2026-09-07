# --- DNK-MRH-HEADER ---
# mrh_id: "docs/api-docs.md"
# purpose: "Canonical REST, SSE Streaming and WebSocket API Documentation for DNK OS MVP."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "3.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# DNK OS API Documentation

Official API reference and developer specifications for **DNK OS Multi-Agent Core**.

---

## 🌐 Base URL
```http
http://localhost:80
```

---

## 🔐 Authentication & Workspace Headers
All secured endpoints require valid JWT authentication and tenant/workspace headers:

```http
Authorization: Bearer <JWT_TOKEN>
X-Workspace-UUID: <RFC4122-UUID>
```

- **Bearer Token**: Standard HMAC-SHA256 or RS256 JWT issued by DNK OS auth service.
- **X-Workspace-UUID**: Required RFC 4122 compliant UUID identifying the isolated workspace context (e.g. `ws-alpha-001` / `123e4567-e89b-12d3-a456-426614174000`).

---

## 📡 Endpoints

### 1. POST `/api/generate`
**Description:** Generates structured completions or task orchestrations using the multi-agent pipeline and framework adapters.

#### Request Headers:
```http
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
X-Workspace-UUID: <RFC4122-UUID>
```

#### Request Body:
```json
{
  "prompt": "Hello, how are",
  "max_tokens": 50,
  "temperature": 0.7,
  "stream": true
}
```

#### Response (200 OK):
```json
{
  "status": "success",
  "text": "Generated text for: Hello, how are",
  "prompt": "Hello, how are",
  "max_tokens": 50,
  "tokens_used": 8
}
```

#### Response (400 Bad Request):
```json
{
  "status": "error",
  "error": "Invalid prompt",
  "code": "INVALID_PROMPT"
}
```

---

### 2. POST `/api/rag`
**Description:** Executes a Retrieval-Augmented Generation (RAG) query against vector collections and SCONES memory stores.

#### Request Body:
```json
{
  "query": "What is the capital of France?",
  "documents": ["Paris is the capital of France."],
  "top_k": 3
}
```

#### Response (200 OK):
```json
{
  "status": "success",
  "query": "What is the capital of France?",
  "documents_count": 1,
  "result": "RAG synthesis completed successfully",
  "confidence": 0.98
}
```

---

### 3. GET `/stream/example`
**Description:** Server-Sent Events (SSE) token-level streaming endpoint demonstrating real-time agent output.

#### Request Headers:
```http
Accept: text/event-stream
```

#### Response (200 OK — `text/event-stream`):
```text
data: {"step": 1, "message": "This is an example of token-level streaming in DNK OS Multi-Agent Core."}

data: {"step": 2, "message": "Streaming chunk 2"}

data: {"step": 3, "message": "Streaming chunk 3"}
```

---

### 4. GET `/health`
**Description:** Multi-tier system health check verifying API workers, PostgreSQL connections, Redis cache, memory, CPU, and disk availability.

#### Response (200 OK):
```json
{
  "status": "healthy",
  "services": {
    "api": {
      "status": "healthy",
      "service": "dnk-api"
    },
    "database": {
      "status": "healthy",
      "latency_ms": 5,
      "connection": "active"
    },
    "redis": {
      "status": "healthy",
      "latency_ms": 2,
      "connection": "active"
    },
    "memory": {
      "status": "healthy",
      "usage_percent": 27.8,
      "available_mb": 2827
    },
    "cpu": {
      "status": "healthy",
      "usage_percent": 1.3,
      "cores": 8
    },
    "disk": {
      "status": "healthy",
      "usage_percent": 16.2,
      "free_gb": 24.89
    }
  }
}
```

---

### 5. GET `/`
**Description:** API root status and version information.

#### Response (200 OK):
```json
{
  "name": "DNK OS Multi-Agent Core",
  "version": "2.2.0",
  "status": "running"
}
```

---

## ⚠️ Error Handling

DNK OS uses unified, predictable JSON error envelopes for all 4xx and 5xx responses.

### Error Codes

| Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `INVALID_PROMPT` | `400` | Invalid, empty, or malformed prompt parameter |
| `UNAUTHORIZED` | `401` | Missing, expired, or cryptographically invalid JWT token |
| `FORBIDDEN` | `403` | Unauthorized workspace UUID or insufficient RBAC privileges |
| `NOT_FOUND` | `404` | Target resource, task ID, or session does not exist |
| `RATE_LIMITED` | `429` | Request threshold exceeded for current time window |
| `INTERNAL_ERROR` | `500` | Uncaught internal server exception or worker failure |

### Error Response Format
```json
{
  "status": "error",
  "error": "Error message description",
  "code": "ERROR_CODE"
}
```

---

## ⏱️ Rate Limiting

Rate limiting is enforced at the Nginx reverse proxy level per client IP address.

### Rate Limits by Endpoint

| Endpoint | Limit | Window | Burst Allowance |
| :--- | :--- | :--- | :--- |
| `/api/generate` | 100 req/min | 60s | 10 req |
| `/api/rag` | 50 req/min | 60s | 5 req |
| `/stream/example` | 200 req/min | 60s | 20 req |
| `/health` | 1000 req/min | 60s | 50 req |

### Rate Limit Response (429 Too Many Requests)
```json
{
  "status": "error",
  "error": "Rate limit exceeded",
  "code": "RATE_LIMITED",
  "retry_after": 60
}
```
