# This import must be first to ensure environment variables are loaded
# before any other module that might need them (like firebase_service).
from .core import config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

# Create the FastAPI app instance
app = FastAPI()

# --- Proxy Headers Middleware ---
# Cloud Run terminates SSL at the load balancer, so we need to trust the
# X-Forwarded-Proto header to know if the original request was HTTPS.
# Without this, FastAPI generates HTTP redirects instead of HTTPS.
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

# --- Middleware ---
# This is a crucial step for allowing the frontend to communicate with this backend.
# Replace "http://localhost:3000" with the actual origin of your frontend app
# in a production environment. For development, this is a common default.
origins = [
    "http://localhost:3000",
    "http://localhost:5173",  # Default for Vite/Vue
    "https://ai-imposter-6368c.web.app",  # Firebase Hosting
    "https://ai-imposter-6368c.firebaseapp.com",  # Firebase Hosting (alternate)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---
# This is a simple "health check" endpoint. It allows us to visit a URL
# (like http://127.0.0.1:8000/ping) to confirm that our server is running.
@app.get("/ping")
def ping():
    """A simple endpoint to check if the server is alive."""
    return {"message": "pong"}

# Debug endpoint to test authentication
from app.api.deps import get_current_user
from fastapi import Depends

@app.get("/debug/auth")
def debug_auth(user_uid: str = Depends(get_current_user)):
    """Debug endpoint to test if authentication is working."""
    return {"authenticated": True, "user_uid": user_uid, "message": "Authentication successful!"}

# Include the API router from the games endpoint file.
# All routes defined in games.py will now be part of our main app,
# prefixed with /api/v1/games
from app.api.endpoints import games
app.include_router(games.router, prefix="/api/v1/games", tags=["Games"])
from app.api.endpoints import models
app.include_router(models.router, prefix="/api/v1/models", tags=["Models"])
