# Cloud Infrastructure Documentation

**Last Updated:** October 30, 2025
**Project:** AI Impostor Game (Reverse Turing Test)
**GCP Project ID:** `ai-imposter-6368c`

This document provides a complete overview of the cloud infrastructure, deployment architecture, and operational details for the AI Impostor Game.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Google Cloud Platform Services](#google-cloud-platform-services)
3. [Frontend Deployment](#frontend-deployment)
4. [Backend Deployment](#backend-deployment)
5. [Database Infrastructure](#database-infrastructure)
6. [Analytics Pipeline](#analytics-pipeline)
7. [Security & Secrets Management](#security--secrets-management)
8. [Networking & CORS](#networking--cors)
9. [Monitoring & Logging](#monitoring--logging)
10. [Deployment Procedures](#deployment-procedures)
11. [Cost Optimization](#cost-optimization)
12. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  Browser                                                        │
│  └─ Vue.js SPA (https://ai-imposter-6368c.web.app)            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FIREBASE SERVICES                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌─────────────────────────────────────┐ │
│  │Firebase Hosting  │  │ Firebase Authentication             │ │
│  │ (Static Assets)  │  │ (Anonymous Auth)                    │ │
│  └──────────────────┘  └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
┌─────────────────────┐  ┌──────────────────────────────────────┐
│   Cloud Run         │  │      Firestore (Real-time DB)        │
│   (Backend API)     │  │  ┌────────────────────────────────┐  │
│                     │  │  │ game_rooms/                    │  │
│ FastAPI + Uvicorn   │◄─┼──│ game_results/                  │  │
│ Python 3.11         │  │  │ {gameId}/messages/             │  │
│                     │  │  └────────────────────────────────┘  │
│ Endpoint:           │  └──────────────────────────────────────┘
│ reverse-turing-     │                    │
│ backend-*.run.app   │                    │ onCreate trigger
└─────────────────────┘                    │
         │                                 ▼
         │                    ┌──────────────────────────────┐
         │                    │  Cloud Functions (Gen 2)     │
         │                    │  Function: archive-game      │
         │                    │  Trigger: Firestore onCreate │
         │                    │  Runtime: Python 3.11        │
         │                    └──────────────────────────────┘
         │                                 │
         │                                 │ Streams data
         ▼                                 ▼
┌─────────────────────┐         ┌──────────────────────────────┐
│  Secret Manager     │         │   BigQuery (Analytics)       │
│                     │         │  Dataset: game_analytics_*   │
│ • openai-api-key    │         │  Table: game_analytics       │
│ • langsmith-api-key │         │                              │
└─────────────────────┘         └──────────────────────────────┘
                                             │
                                             │ Queries
                                             ▼
                                ┌──────────────────────────────┐
                                │    Looker Studio             │
                                │    (Dashboards)              │
                                └──────────────────────────────┘
```

### Service Responsibilities

| Service | Purpose | Scalability | Cost Model |
|---------|---------|-------------|-----------|
| **Firebase Hosting** | Serve frontend static files | Auto-scales | Free tier (10GB/month) |
| **Cloud Run** | Host FastAPI backend | Auto-scales 0→N | Pay-per-request + compute time |
| **Firestore** | Real-time game state | Auto-scales | Per read/write/storage |
| **Firebase Auth** | Anonymous user authentication | Auto-scales | Free tier (10K/month) |
| **Cloud Functions** | ETL data pipeline | Auto-scales | Per invocation + compute time |
| **BigQuery** | Analytics warehouse | Managed | Per query (TB scanned) + storage |
| **Secret Manager** | API key storage | N/A | Per secret + access |

---

## Google Cloud Platform Services

### Project Configuration

```bash
# Project Details
PROJECT_ID="ai-imposter-6368c"
PROJECT_NUMBER="611852534045"
REGION="asia-northeast3"  # Seoul (backend)
BIGQUERY_REGION="us-central1"  # Analytics data
```

### Enabled APIs

```bash
# Core Services
- run.googleapis.com                    # Cloud Run
- firestore.googleapis.com             # Firestore
- cloudbuild.googleapis.com            # Container builds
- cloudfunctions.googleapis.com        # Cloud Functions
- bigquery.googleapis.com              # BigQuery
- secretmanager.googleapis.com         # Secret Manager
- firebase.googleapis.com              # Firebase services
- artifactregistry.googleapis.com      # Container Registry (GCR)
```

### Service Accounts

**Default Compute Service Account:**
- Email: `611852534045-compute@developer.gserviceaccount.com`
- Used by: Cloud Run, Cloud Functions
- Permissions:
  - Secret Manager Secret Accessor (for API keys)
  - Firestore User (read/write game data)
  - BigQuery Data Editor (write analytics)

---

## Frontend Deployment

### Firebase Hosting Configuration

**Hosting URL:**
- Primary: `https://ai-imposter-6368c.web.app`
- Alternate: `https://ai-imposter-6368c.firebaseapp.com`

**Build Configuration:**

```json
// firebase.json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

**Environment Variables (Build-time):**

Location: `frontend/.env`

```bash
# Firebase Configuration
VITE_API_KEY="AIzaSyBWyrhmmniVFEkI5bmzNDSYnj3qvOuSxA4"
VITE_AUTH_DOMAIN="ai-imposter-6368c.firebaseapp.com"
VITE_PROJECT_ID="ai-imposter-6368c"
VITE_STORAGE_BUCKET="ai-imposter-6368c.firebasestorage.app"
VITE_MESSAGING_SENDER_ID="611852534045"
VITE_APP_ID="1:611852534045:web:e9ae2a8a765857a3dda1f4"
VITE_MEASUREMENT_ID="G-Z6SLH0Y0CF"

# Backend API Endpoint
VITE_API_BASE_URL="https://reverse-turing-backend-611852534045.asia-northeast3.run.app"
```

**Build & Deploy Process:**

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Build production bundle (embeds .env variables)
npm run build-only

# 4. Deploy to Firebase Hosting
firebase deploy --only hosting

# Output: Frontend deployed to https://ai-imposter-6368c.web.app
```

**Key Characteristics:**
- **Static Site**: Pre-rendered Vue.js SPA
- **CDN**: Global edge caching via Firebase CDN
- **Auto-scaling**: Unlimited concurrent users
- **HTTPS**: Automatic SSL certificate
- **Build-time Configuration**: Environment variables embedded during build

---

## Backend Deployment

### Cloud Run Configuration

**Service Details:**
- Service Name: `reverse-turing-backend`
- Region: `asia-northeast3` (Seoul, South Korea)
- URL: `https://reverse-turing-backend-611852534045.asia-northeast3.run.app`
- Authentication: Allow unauthenticated (CORS handles security)

**Container Configuration:**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Copy dependencies
COPY pyproject.toml ./
RUN uv pip install --system --no-cache .

# Copy application code
COPY ./app ./app

# Cloud Run configuration
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:${PORT}/ping')"

# Run with Uvicorn
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
```

**Runtime Environment:**
- **Runtime**: Python 3.11 (slim)
- **ASGI Server**: Uvicorn
- **Framework**: FastAPI
- **Port**: 8080 (injected by Cloud Run)
- **Concurrency**: 80 requests per container instance
- **CPU**: 1 vCPU (default)
- **Memory**: 512 MiB (default)
- **Timeout**: 300s request timeout
- **Min Instances**: 0 (scales to zero)
- **Max Instances**: 100 (configurable)

**Environment Secrets (Runtime):**

Secrets are injected from Secret Manager at container startup:

```bash
# Configured via gcloud deploy command
--set-secrets=OPENAI_API_KEY=openai-api-key:latest
--set-secrets=LANGSMITH_API_KEY=langsmith-api-key:latest
```

Backend code accesses via:
```python
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

**Build & Deploy Process:**

```bash
# 1. Navigate to backend directory
cd backend

# 2. Build Docker image using Cloud Build
gcloud builds submit --tag gcr.io/ai-imposter-6368c/reverse-turing-backend:latest

# 3. Deploy to Cloud Run
gcloud run deploy reverse-turing-backend \
  --image gcr.io/ai-imposter-6368c/reverse-turing-backend:latest \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --set-secrets=OPENAI_API_KEY=openai-api-key:latest,LANGSMITH_API_KEY=langsmith-api-key:latest

# Output: Service deployed and serving traffic
```

**Auto-scaling Behavior:**

```
Requests/sec │
             │
    High ────┤     ┌─────┐
             │     │     │
  Medium ────┤   ┌─┘     └─┐
             │   │         │
     Low ────┤ ┌─┘         └─┐
             │ │             │
    Zero ────┼─┘             └──────
             └────────────────────── Time

Instances    0 → 1 → 3 → 1 → 0
```

**Key Characteristics:**
- **Serverless**: Scales to zero when idle
- **HTTPS Termination**: Load balancer terminates SSL
- **Request Routing**: Load balancer distributes requests
- **Health Checks**: `/ping` endpoint for liveness
- **Container Registry**: Images stored in GCR

---

## Database Infrastructure

### Firestore (Real-time Database)

**Configuration:**
- **Database**: `(default)`
- **Mode**: Native mode
- **Location**: `us-central` (multi-region)
- **Rules**: Production mode (authenticated access only)

**Collections:**

| Collection | Purpose | Estimated Size | TTL |
|-----------|---------|----------------|-----|
| `game_rooms` | Active game state | ~10-100 docs | Manual cleanup |
| `game_rooms/{id}/messages` | Round answers | ~20-100 per game | Cascade delete |
| `game_results` | Completed games (archive) | Growing | 7 days |
| `failed_archives` | Pipeline errors | Rare | Manual review |

**Security Rules:**

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Authenticated users only
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

**Real-time Listeners:**

Frontend uses `onSnapshot` for live updates:
- `game_rooms/{gameId}` - Game state changes
- `game_rooms/{gameId}/messages` - New answers/messages

**Indexes:**

```yaml
# Auto-generated indexes
indexes:
  - collectionGroup: messages
    queryScope: COLLECTION
    fields:
      - fieldPath: roundNumber
        order: ASCENDING
      - fieldPath: timestamp
        order: ASCENDING
```

### BigQuery (Analytics Warehouse)

**Dataset:**
- Dataset ID: `game_analytics_dataset`
- Location: `us-central1`
- Description: "AI Impostor Game Analytics Data"
- Default table expiration: None (permanent storage)

**Table: game_analytics**

Schema: See `backend/bigquery_schema.json`

Key Fields:
- `gameId` (STRING, REQUIRED) - Primary key
- `endedAt` (TIMESTAMP, REQUIRED) - Partitioning key
- `aiModelUsed` (STRING, REQUIRED) - Clustering key
- `winner` (STRING, REQUIRED) - humans or ai
- `players` (REPEATED RECORD) - Nested player data
- `rounds` (REPEATED RECORD) - Questions and answers
- `votes` (REPEATED RECORD) - Vote history
- `lastRoundResult` (RECORD) - Game outcome summary

**Partitioning & Clustering:**

```sql
-- Future optimization for large datasets
CREATE TABLE game_analytics_dataset.game_analytics_v2
PARTITION BY DATE(endedAt)
CLUSTER BY aiModelUsed, winner
AS SELECT * FROM game_analytics_dataset.game_analytics;
```

**Storage:**
- Current: <1 GB (early stage)
- Estimated growth: ~100 MB/month (1000 games)
- Long-term storage: BigQuery compression reduces costs

---

## Analytics Pipeline

### Pipeline Architecture

```
Game Ends
    ↓
Backend: _archive_game_result()
    ↓
Firestore: game_results/{gameId} created
    ↓ [Firestore Trigger]
Cloud Function: archive-game
    ↓
Transform Firestore → BigQuery format
    ↓
BigQuery: streaming insert
    ↓
Looker Studio: dashboard auto-updates
```

### Cloud Function: archive-game

**Configuration:**
- Function Name: `archive-game`
- Region: `us-central1`
- Generation: 2nd gen
- Runtime: Python 3.11
- Entry Point: `archive_game`
- Memory: 512 MB
- Timeout: 60 seconds
- Max Instances: 10
- Min Instances: 0

**Trigger:**
```yaml
Event Type: google.cloud.firestore.document.v1.created
Database: (default)
Document Pattern: game_results/{documentId}
```

**Dependencies:**
```txt
functions-framework==3.*
google-cloud-bigquery==3.*
google-events>=0.7.0
```

**Deployment Command:**
```bash
cd backend/cloud_functions/archive_game

gcloud functions deploy archive-game \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=archive_game \
  --trigger-event-filters="type=google.cloud.firestore.document.v1.created" \
  --trigger-event-filters="database=(default)" \
  --trigger-location=us-central1 \
  --trigger-event-filters-path-pattern="document=game_results/{documentId}" \
  --max-instances=10 \
  --timeout=60s \
  --memory=512MB
```

**Error Handling:**
- Automatic retries on failure (Cloud Functions default)
- Errors logged to Cloud Logging
- Failed archives stored in `failed_archives` collection (future)

**Performance:**
- Typical latency: 1-3 seconds
- Max latency (cold start): 10-15 seconds
- Throughput: 100+ games/minute

---

## Security & Secrets Management

### Secret Manager

**Stored Secrets:**

| Secret Name | Purpose | Access |
|------------|---------|--------|
| `openai-api-key` | OpenAI API authentication | Cloud Run backend |
| `langsmith-api-key` | LangSmith tracing | Cloud Run backend |

**IAM Configuration:**

```bash
# Grant service account access
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:611852534045-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding langsmith-api-key \
  --member="serviceAccount:611852534045-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**Security Best Practices:**
- ✅ Secrets never committed to Git
- ✅ Secrets injected at runtime (not build time)
- ✅ IAM controls who can access secrets
- ✅ Audit logs track secret access
- ✅ Automatic secret rotation supported

### Firebase Authentication

**Authentication Method:**
- **Type**: Anonymous Authentication
- **Purpose**: Generate unique UIDs without user credentials
- **User Experience**: Frictionless - no login required
- **Security**: Each browser session gets unique UID
- **Backend Verification**: ID tokens validated by Firebase Admin SDK

**Authentication Flow:**

```
User Opens App
    ↓
Frontend: signInAnonymously()
    ↓
Firebase Auth: Generate UID + ID Token
    ↓
Frontend: Include token in API requests
    ↓
Backend: Verify token → Extract UID
    ↓
Backend: Use UID for game operations
```

**Token Validation (Backend):**

```python
# app/api/deps.py
from firebase_admin import auth

async def get_current_user(authorization: str = Header(None)):
    """Dependency to extract authenticated user from Firebase token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401)

    token = authorization.split("Bearer ")[1]
    decoded_token = auth.verify_id_token(token)
    return decoded_token['uid']
```

---

## Networking & CORS

### CORS Configuration

**Backend (main.py):**

```python
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",                    # Local dev
    "http://localhost:5173",                    # Vite dev server
    "https://ai-imposter-6368c.web.app",        # Firebase Hosting (primary)
    "https://ai-imposter-6368c.firebaseapp.com" # Firebase Hosting (alternate)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**How CORS Works:**

```
1. Browser Preflight Request (OPTIONS):
   Origin: https://ai-imposter-6368c.web.app

2. Backend Response:
   Access-Control-Allow-Origin: https://ai-imposter-6368c.web.app
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE
   Access-Control-Allow-Headers: *
   Access-Control-Allow-Credentials: true

3. Browser Sends Actual Request:
   GET /api/v1/games
   Origin: https://ai-imposter-6368c.web.app

4. Backend Response:
   Access-Control-Allow-Origin: https://ai-imposter-6368c.web.app
   [actual game data]
```

### Proxy Headers Middleware

**Issue**: Cloud Run terminates SSL, causing FastAPI to generate HTTP redirects.

**Solution**: `ProxyHeadersMiddleware` trusts `X-Forwarded-Proto` header.

```python
class ProxyHeadersMiddleware:
    """Fixes HTTPS redirects behind Cloud Run load balancer."""

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            headers = Headers(scope=scope)
            forwarded_proto = headers.get("x-forwarded-proto")
            if forwarded_proto:
                scope["scheme"] = forwarded_proto  # "https"
        await self.app(scope, receive, send)

app.add_middleware(ProxyHeadersMiddleware)
```

**Why This Matters:**
- Without it: Backend generates `http://` redirect URLs
- Browser blocks: Mixed content (HTTPS → HTTP)
- With it: Backend generates `https://` redirect URLs
- Browser allows: Same protocol (HTTPS → HTTPS)

See: `docs/troubleshooting.md#issue-1` for complete analysis.

---

## Monitoring & Logging

### Cloud Logging

**Log Locations:**

| Service | Log Path | Query |
|---------|---------|-------|
| Cloud Run | `projects/ai-imposter-6368c/logs/run.googleapis.com%2Fstdout` | `resource.type="cloud_run_revision"` |
| Cloud Functions | `projects/ai-imposter-6368c/logs/cloudfunctions.googleapis.com` | `resource.type="cloud_function"` |
| Cloud Build | `projects/ai-imposter-6368c/logs/cloudbuild.googleapis.com` | `resource.type="build"` |

**Useful Queries:**

```bash
# Backend errors
resource.type="cloud_run_revision"
resource.labels.service_name="reverse-turing-backend"
severity>=ERROR

# Cloud Function errors
resource.type="cloud_function"
resource.labels.function_name="archive-game"
severity>=ERROR

# Successful archives
resource.type="cloud_function"
textPayload=~"Successfully archived game"
```

### Health Monitoring

**Backend Health Check:**
```bash
curl https://reverse-turing-backend-611852534045.asia-northeast3.run.app/ping
# Expected: {"message": "pong"}
```

**Frontend Health Check:**
```bash
curl -I https://ai-imposter-6368c.web.app
# Expected: HTTP/2 200
```

**Cloud Function Health:**
```bash
gcloud functions describe archive-game --region=us-central1
# Expected: status: ACTIVE
```

### Cost Monitoring

**GCP Console Dashboard:**
- https://console.cloud.google.com/billing/

**Key Metrics to Track:**
- Cloud Run: Request count, compute time
- Firestore: Read/write operations, storage
- BigQuery: Query bytes processed, storage
- Cloud Functions: Invocations, compute time

---

## Deployment Procedures

### Full Application Deployment

**Prerequisites:**
```bash
# Install tools
npm install -g firebase-tools
# Install gcloud CLI: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
firebase login
```

**Step-by-Step Deployment:**

```bash
# ===== 1. UPDATE SECRETS (if needed) =====
gcloud secrets versions add openai-api-key --data-file=-
# Paste API key, then Ctrl+D

gcloud secrets versions add langsmith-api-key --data-file=-
# Paste API key, then Ctrl+D

# ===== 2. DEPLOY BACKEND =====
cd backend

# Build Docker image
gcloud builds submit --tag gcr.io/ai-imposter-6368c/reverse-turing-backend:latest

# Deploy to Cloud Run
gcloud run deploy reverse-turing-backend \
  --image gcr.io/ai-imposter-6368c/reverse-turing-backend:latest \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --set-secrets=OPENAI_API_KEY=openai-api-key:latest,LANGSMITH_API_KEY=langsmith-api-key:latest

# Note the service URL from output

# ===== 3. UPDATE FRONTEND CONFIG =====
cd ../frontend

# Edit .env file
# Set VITE_API_BASE_URL to Cloud Run URL from step 2

# ===== 4. DEPLOY FRONTEND =====
# Build production bundle
npm run build-only

# Deploy to Firebase Hosting
firebase deploy --only hosting

# ===== 5. VERIFY DEPLOYMENT =====
# Test backend
curl https://reverse-turing-backend-611852534045.asia-northeast3.run.app/ping

# Test frontend
open https://ai-imposter-6368c.web.app
```

### Rollback Procedures

**Backend Rollback:**
```bash
# List revisions
gcloud run revisions list --service=reverse-turing-backend --region=asia-northeast3

# Rollback to specific revision
gcloud run services update-traffic reverse-turing-backend \
  --region=asia-northeast3 \
  --to-revisions=reverse-turing-backend-00003-xyz=100
```

**Frontend Rollback:**
```bash
# List deployment history
firebase hosting:channel:list

# Rollback to previous deployment
firebase hosting:clone SOURCE_SITE_ID:SOURCE_CHANNEL_ID TARGET_SITE_ID:live
```

---

## Cost Optimization

### Current Cost Structure (MVP)

**Estimated Monthly Costs** (100 games/day, 3000 games/month):

| Service | Usage | Cost |
|---------|-------|------|
| Cloud Run | ~10,000 requests, 2 hours compute | $0.50 |
| Firestore | 100K reads, 50K writes, 1GB storage | $1.50 |
| BigQuery | 100MB storage, 10MB scanned/day | $0.10 |
| Cloud Functions | 3000 invocations, 30 seconds total | $0.20 |
| Firebase Hosting | 10GB bandwidth, 1GB storage | Free |
| Secret Manager | 2 secrets, 10K accesses | $0.20 |
| **Total** | | **~$2.50/month** |

### Cost Optimization Strategies

**Free Tier Eligible:**
- ✅ Cloud Run: 2M requests/month free
- ✅ Firestore: 50K reads, 20K writes/day free
- ✅ Cloud Functions: 2M invocations/month free
- ✅ Firebase Hosting: 10GB bandwidth/month free
- ✅ BigQuery: 1TB queries/month free

**Scale-up Cost Estimates:**

| Scale | Games/Month | Estimated Cost |
|-------|-------------|----------------|
| MVP | 3,000 | $2.50 |
| Beta | 10,000 | $8.00 |
| Launch | 100,000 | $80.00 |
| Growth | 1,000,000 | $800.00 |

**Optimization Recommendations:**
1. **Cloud Run**: Increase min instances if cold starts become issue
2. **Firestore**: Implement caching for frequently read data
3. **BigQuery**: Use partitioning/clustering for large datasets
4. **Cloud Functions**: Increase memory if execution time is high

---

## Troubleshooting

### Common Issues

#### 1. Frontend Can't Connect to Backend

**Symptoms:**
- API requests fail with CORS errors
- Mixed content warnings in console

**Diagnosis:**
```bash
# Check if backend is running
curl https://reverse-turing-backend-611852534045.asia-northeast3.run.app/ping

# Check CORS headers
curl -I -X OPTIONS https://reverse-turing-backend-611852534045.asia-northeast3.run.app/api/v1/games \
  -H "Origin: https://ai-imposter-6368c.web.app"
```

**Solutions:**
1. Verify frontend `.env` has correct `VITE_API_BASE_URL`
2. Rebuild frontend after `.env` changes
3. Check backend CORS allows frontend origin
4. See `docs/troubleshooting.md#issue-1` for HTTPS redirect issues

#### 2. Cloud Function Not Triggering

**Symptoms:**
- Games complete but don't appear in BigQuery
- No function logs in Cloud Logging

**Diagnosis:**
```bash
# Check function status
gcloud functions describe archive-game --region=us-central1

# Check recent logs
gcloud functions logs read archive-game --region=us-central1 --limit=20

# Check if game_results document was created
# (View in Firestore console)
```

**Solutions:**
1. Verify trigger configuration matches `game_results` collection
2. Check IAM permissions for service account
3. Test manually by creating a `game_results` document
4. Check function error logs for exceptions

#### 3. Secret Access Denied

**Symptoms:**
- Cloud Run logs show "Permission denied" for secrets
- Backend can't access API keys

**Diagnosis:**
```bash
# Check IAM policy
gcloud secrets get-iam-policy openai-api-key
```

**Solutions:**
```bash
# Grant access to service account
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:611852534045-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### 4. Container Build Failures

**Symptoms:**
- `gcloud builds submit` fails
- Dependency installation errors

**Diagnosis:**
```bash
# View build logs
gcloud builds list --limit=5
gcloud builds log [BUILD_ID]
```

**Solutions:**
1. Check `pyproject.toml` for invalid dependencies
2. Verify Dockerfile syntax
3. Ensure `uv` can resolve dependencies
4. Check Cloud Build service account permissions

---

## Quick Reference Commands

```bash
# ===== PROJECT CONFIGURATION =====
gcloud config set project ai-imposter-6368c
gcloud config set run/region asia-northeast3

# ===== BACKEND OPERATIONS =====
# Deploy backend
cd backend && gcloud builds submit --tag gcr.io/ai-imposter-6368c/reverse-turing-backend:latest
gcloud run deploy reverse-turing-backend --image gcr.io/ai-imposter-6368c/reverse-turing-backend:latest

# View backend logs
gcloud run services logs read reverse-turing-backend --region=asia-northeast3

# ===== FRONTEND OPERATIONS =====
# Deploy frontend
cd frontend && npm run build-only && firebase deploy --only hosting

# ===== CLOUD FUNCTION OPERATIONS =====
# Deploy function
cd backend/cloud_functions/archive_game
gcloud functions deploy archive-game [options]

# View function logs
gcloud functions logs read archive-game --region=us-central1

# ===== DATABASE OPERATIONS =====
# Query BigQuery
bq query --use_legacy_sql=false 'SELECT * FROM game_analytics_dataset.game_analytics LIMIT 10'

# ===== MONITORING =====
# Open Cloud Console
open https://console.cloud.google.com/logs/query?project=ai-imposter-6368c
open https://console.cloud.google.com/run?project=ai-imposter-6368c
```

---

## Related Documentation

- [Analytics Pipeline Implementation](./analytics_pipeline_implementation.md) - Detailed pipeline setup
- [Troubleshooting Guide](./troubleshooting.md) - Common issues and solutions
- [Backend Blueprint](./backend_blueprint.md) - Backend architecture
- [Database Schema](./database_schema.md) - Firestore and BigQuery schemas
- [Development Notes](./dev_notes.md) - Architectural decisions

---

**Document Status:** Production deployment documented as of October 30, 2025.
