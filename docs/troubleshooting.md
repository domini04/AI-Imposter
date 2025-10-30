# Troubleshooting Guide

This document records significant issues encountered during development and their solutions.

---

## Issue #1: Mixed Content Error - HTTP Redirects from HTTPS Backend

**Date:** 2025-10-30
**Severity:** Critical - Blocked all frontend-backend communication in production
**Status:** ✅ Resolved

### Problem Statement

After deploying the backend to Cloud Run and frontend to Firebase Hosting, the frontend was unable to communicate with the backend. The application worked perfectly in local development but completely failed in production.

**Error Symptoms:**
```
혼합된 액티브 콘텐츠 "http://reverse-turing-backend-611852534045.asia-northeast3.run.app/api/v1/models/" 로드를 차단함
(Blocked loading mixed active content "http://...")

교차 출처 요청 차단: 동일 출처 정책으로 인해 https://reverse-turing-backend-611852534045.asia-northeast3.run.app/api/v1/models에 있는 원격 리소스를 차단했습니다.
(CORS request did not succeed)
```

**User Impact:**
- AI models dropdown showed "No AI models available"
- Could not create games
- All API requests from frontend failed silently

### Root Cause Analysis

The error message mentioned "CORS" but **CORS was correctly configured**. The real issue was a **mixed content violation** caused by FastAPI generating HTTP redirects when it should generate HTTPS redirects.

#### The Request Flow (Before Fix)

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Frontend Makes Request                                  │
│ Browser: https://ai-imposter-6368c.web.app                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS Request
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: Cloud Run Load Balancer                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ • Receives: HTTPS (encrypted)                               │ │
│ │ • Terminates SSL/TLS (decrypts)                             │ │
│ │ • Adds headers:                                             │ │
│ │   X-Forwarded-Proto: https  ← Records original protocol    │ │
│ │   X-Forwarded-For: <client-ip>                             │ │
│ │ • Forwards to container: HTTP (unencrypted, internal)      │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP Request (internal network)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: Container (Uvicorn)                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Receives HTTP request:                                      │ │
│ │   GET /api/v1/models HTTP/1.1                               │ │
│ │   Host: backend...                                          │ │
│ │   X-Forwarded-Proto: https                                  │ │
│ │                                                             │ │
│ │ Creates ASGI scope:                                         │ │
│ │   scope = {                                                 │ │
│ │     "scheme": "http",    ← Problem: Uvicorn only sees HTTP │ │
│ │     "path": "/api/v1/models",                               │ │
│ │     "headers": [                                            │ │
│ │       (b"x-forwarded-proto", b"https"),  ← Clue ignored!   │ │
│ │     ]                                                       │ │
│ │   }                                                         │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: FastAPI Routing                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Requested: /api/v1/models (no trailing slash)              │ │
│ │ Defined:   /api/v1/models/ (with trailing slash)           │ │
│ │                                                             │ │
│ │ FastAPI generates redirect:                                 │ │
│ │   redirect_url = f"{scope['scheme']}://{host}{path}/"      │ │
│ │   redirect_url = "http://backend.../api/v1/models/"        │ │
│ │                   ^^^^                                      │ │
│ │                   Uses HTTP because scope["scheme"] = "http"│ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Returns: HTTP 307 Temporary Redirect
                              │ Location: http://backend.../api/v1/models/
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Browser Receives Redirect                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Original: https://backend.../api/v1/models                  │ │
│ │ Redirect: http://backend.../api/v1/models/                  │ │
│ │                                                             │ │
│ │ Browser Security Check:                                     │ │
│ │   ❌ HTTPS page trying to load HTTP resource               │ │
│ │   ❌ MIXED CONTENT VIOLATION                               │ │
│ │   ❌ BLOCK REQUEST                                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Error Reported to Console                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ "Blocked loading mixed active content"                      │ │
│ │ "CORS request did not succeed" ← Misleading!                │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### Why the Error Message Was Misleading

The browser reported "CORS request did not succeed" but **CORS was not the problem**:

1. The request was blocked **before** it could be completed
2. The browser couldn't access the actual error (security reasons)
3. It defaulted to reporting a generic "CORS" error

**Actual problem:** Mixed content violation (HTTPS → HTTP redirect)
**Reported problem:** CORS failure

---

### Core Concepts

#### 1. SSL/TLS Termination

**What is SSL Termination?**

SSL termination is when a proxy (like a load balancer) decrypts HTTPS traffic before forwarding it to backend servers.

```
┌──────────┐  Encrypted   ┌─────────────┐  Unencrypted  ┌──────────┐
│  Client  │────HTTPS────►│Load Balancer│─────HTTP─────►│ Backend  │
│ (Browser)│              │(Terminates  │               │(Container)│
│          │              │    SSL)     │               │          │
└──────────┘              └─────────────┘               └──────────┘
```

**Why do this?**
- **Performance**: Encryption/decryption is CPU-intensive. Doing it once at the edge is more efficient.
- **Centralized Certificates**: Manage SSL certificates in one place instead of on every backend server.
- **Load Balancer Features**: Enables HTTP-level routing, header inspection, and health checks.

**The Trade-off**: Backend servers lose visibility into the original protocol (HTTP vs HTTPS).

#### 2. X-Forwarded Headers

To preserve information lost during SSL termination, load balancers add **X-Forwarded-*** headers:

| Header | Purpose | Example |
|--------|---------|---------|
| `X-Forwarded-Proto` | Original protocol (http/https) | `https` |
| `X-Forwarded-For` | Original client IP | `203.0.113.42` |
| `X-Forwarded-Host` | Original host header | `api.example.com` |
| `X-Forwarded-Port` | Original port | `443` |

**Example HTTP Request to Container:**
```http
GET /api/v1/models HTTP/1.1
Host: backend.run.app
X-Forwarded-Proto: https        ← Original protocol
X-Forwarded-For: 203.0.113.42   ← Client's real IP
User-Agent: Mozilla/5.0
```

**Security Note**: Only trust these headers when behind a **trusted proxy** (like Cloud Run). Public-facing servers should ignore them as clients can forge these headers.

#### 3. The `scope` Dictionary

**The `scope` Dictionary:**

The `scope` is the core data structure that flows through your application. It contains all request metadata:

```python
scope = {
    # Request type
    "type": "http",                    # or "websocket", "lifespan"

    # HTTP details
    "method": "GET",
    "scheme": "http",                  # ← The key field for our issue
    "path": "/api/v1/models",
    "query_string": b"",
    "http_version": "1.1",

    # Headers (as list of byte tuples)
    "headers": [
        (b"host", b"backend.run.app"),
        (b"x-forwarded-proto", b"https"),  # ← The clue!
        (b"user-agent", b"Mozilla/5.0"),
    ],

    # Server/client info
    "server": ("127.0.0.1", 8080),
    "client": ("10.1.2.3", 54321),
}
```

**How FastAPI Uses `scope["scheme"]`:**

```python
# Pseudocode from Starlette/FastAPI internals
def generate_redirect_url(scope, new_path):
    scheme = scope["scheme"]      # "http" or "https"
    host = get_header(scope, "host")
    return f"{scheme}://{host}{new_path}"

# Example:
# If scope["scheme"] = "http"  → "http://backend.../path"  ❌
# If scope["scheme"] = "https" → "https://backend.../path" ✅
```

#### 4. Middleware Pattern

**What is Middleware?**

Middleware is code that sits **between** the server and your application, wrapping around it like layers of an onion.

**Execution Flow:**

```
Request comes in
    ↓
[Middleware 1] ── before logic ──┐
    ↓                             │
[Middleware 2] ── before logic ──┤
    ↓                             │
[Middleware 3] ── before logic ──┤
    ↓                             │
[Your Application]                │
    ↓                             │
[Middleware 3] ── after logic ───┤
    ↓                             │
[Middleware 2] ── after logic ───┤
    ↓                             │
[Middleware 1] ── after logic ───┘
    ↓
Response goes out
```

**Key Properties:**
1. Each middleware can inspect/modify the request
2. Each middleware can inspect/modify the response
3. Middleware can block requests (return early)
4. Order matters: first added = outermost layer

**Basic Middleware Structure:**

```python
class MyMiddleware:
    def __init__(self, app):
        self.app = app  # Next layer

    async def __call__(self, scope, receive, send):
        # BEFORE: Runs on request coming in
        print("Request received")

        # Pass to next layer
        await self.app(scope, receive, send)

        # AFTER: Runs on response going out
        print("Response sent")
```

---

### The Solution

#### Overview

We implemented a **ProxyHeadersMiddleware** that:
1. Intercepts every incoming request
2. Reads the `X-Forwarded-Proto` header
3. Updates `scope["scheme"]` to match the original protocol
4. Passes the corrected scope to FastAPI

#### Implementation

**File:** `backend/app/main.py`

```python
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

class ProxyHeadersMiddleware:
    """
    Middleware to handle X-Forwarded-Proto header from Cloud Run.

    When running behind a reverse proxy (like Cloud Run's load balancer),
    SSL is terminated at the proxy level. The proxy forwards the request
    to our container via HTTP but includes X-Forwarded-Proto to indicate
    the original protocol.

    This middleware reads that header and updates the ASGI scope so FastAPI
    generates URLs with the correct scheme (https instead of http).
    """
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            headers = Headers(scope=scope)
            # Trust the X-Forwarded-Proto header from Cloud Run's load balancer
            forwarded_proto = headers.get("x-forwarded-proto")
            if forwarded_proto:
                scope["scheme"] = forwarded_proto
        await self.app(scope, receive, send)

# Add the proxy headers middleware BEFORE other middleware
# This ensures all subsequent middleware and FastAPI see the correct scheme
app.add_middleware(ProxyHeadersMiddleware)

# Then add CORS and other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### How It Works (After Fix)

```
┌─────────────────────────────────────────────────────────────────┐
│ Request Flow After Fix                                           │
└─────────────────────────────────────────────────────────────────┘

Frontend Request (HTTPS)
    ↓
Cloud Run Load Balancer
    • Terminates SSL
    • Adds: X-Forwarded-Proto: https
    • Forwards HTTP to container
    ↓
Uvicorn (ASGI Server)
    • Creates scope with scheme="http"
    • Includes headers with X-Forwarded-Proto
    ↓
ProxyHeadersMiddleware ← OUR FIX
    • Reads: X-Forwarded-Proto = "https"
    • Updates: scope["scheme"] = "https"
    • Passes corrected scope to next layer
    ↓
CORSMiddleware
    • Adds CORS headers (works normally)
    ↓
FastAPI Application
    • Uses scope["scheme"] = "https"
    • Generates redirect: https://backend.../api/v1/models/
    • ✅ Correct protocol!
    ↓
Browser
    • Receives: HTTPS → HTTPS redirect
    • ✅ No mixed content violation
    • ✅ Follows redirect successfully
    ↓
API Response
    • ✅ Models data returned
    • ✅ Frontend works!
```

#### Middleware Placement

**Critical:** ProxyHeadersMiddleware must be added **BEFORE** other middleware:

```python
# Correct order:
app.add_middleware(ProxyHeadersMiddleware)  # Fix scheme first
app.add_middleware(CORSMiddleware)          # Then CORS
app.add_middleware(AuthMiddleware)          # Then auth
```

This ensures all subsequent layers see the corrected `scope["scheme"]`.

---

### Verification

#### Test 1: Check Redirect Protocol

**Before fix:**
```bash
$ curl -i https://backend.run.app/api/v1/models
HTTP/2 307
location: http://backend.run.app/api/v1/models/
         ^^^^
         HTTP - Wrong!
```

**After fix:**
```bash
$ curl -i https://backend.run.app/api/v1/models
HTTP/2 307
location: https://backend.run.app/api/v1/models/
         ^^^^^
         HTTPS - Correct!
```

#### Test 2: Frontend Integration

**Before fix:**
- AI models dropdown: "No AI models available"
- Console errors: Mixed content blocked, CORS failure

**After fix:**
- AI models dropdown: Shows available models ✅
- Console: No errors ✅
- Can create and join games ✅

---

### Lessons Learned

#### 1. Error Messages Can Be Misleading

The browser reported "CORS failure" but CORS was correctly configured. The real issue was mixed content blocking. **Always investigate beyond the error message.**

#### 2. Understand Your Infrastructure

Cloud Run's SSL termination behavior is documented but easy to overlook. **Know how your deployment environment modifies requests.**

#### 3. Local vs Production Differences

The issue only appeared in production because:
- Local: Both frontend and backend used HTTP
- Production: Frontend used HTTPS, backend received HTTP internally

**Always test in production-like environments.**

#### 4. Trust Proxy Headers (When Appropriate)

When behind a trusted reverse proxy, you **must** trust forwarded headers. But only do this when you control the proxy - never trust these headers on public-facing servers.

#### 5. Middleware Order Matters

Middleware that modifies the request (like ProxyHeadersMiddleware) should run **before** middleware that uses that data (like CORS, Auth, etc.).

---

### Related Issues

This pattern applies to any FastAPI/Starlette application deployed behind a reverse proxy that terminates SSL:

- **Cloud Run** (Google Cloud) ✅ Covered by this fix
- **App Engine** (Google Cloud) - Same pattern applies
- **AWS Application Load Balancer** - Same pattern applies
- **Nginx reverse proxy** - Same pattern applies
- **Cloudflare** - Same pattern applies

**Key Indicator**: If your logs show the container receiving HTTP but clients connecting via HTTPS, you need this middleware.

---

### References

- [Starlette Middleware Documentation](https://www.starlette.io/middleware/)
- [MDN: Mixed Content](https://developer.mozilla.org/en-US/docs/Web/Security/Mixed_content)
- [RFC 7239: Forwarded HTTP Extension](https://datatracker.ietf.org/doc/html/rfc7239)
- [Cloud Run: SSL Termination](https://cloud.google.com/run/docs/triggering/https-request)
- [ASGI Specification](https://asgi.readthedocs.io/en/latest/specs/main.html)

---

## Issue #2: [Reserved for future troubleshooting cases]

*More issues will be documented here as they are encountered and resolved.*
