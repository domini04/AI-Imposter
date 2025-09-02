from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create the FastAPI app instance
app = FastAPI()

# --- Middleware ---
# This is a crucial step for allowing the frontend to communicate with this backend.
# Replace "http://localhost:3000" with the actual origin of your frontend app
# in a production environment. For development, this is a common default.
origins = [
    "http://localhost:3000",
    "http://localhost:5173", # Default for Vite/Vue
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

# We will later include our game API routes here
# from app.api.endpoints import games
# app.include_router(games.router, prefix="/api/v1")
