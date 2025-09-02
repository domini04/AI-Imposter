# Project Structure

This document outlines the proposed folder and file structure for the AI Impostor Game monorepo.

## 1. High-Level Overview

The project is organized as a monorepo containing two distinct applications:
*   `frontend/`: A Vue.js Single Page Application.
*   `backend/`: A Python FastAPI server.

All project-level design and planning documents are located in the root directory.

## 2. Backend Structure (FastAPI)

The backend will be managed using **`uv`** for dependency management and environment setup.

```
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   └── games.py        # --- API routes for /games, /games/{id}/join, etc.
│   │   └── deps.py             # --- Dependencies for API endpoints (e.g., auth validation)
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # --- Configuration management (environment variables)
│   ├── models/
│   │   ├── __init__.py
│   │   └── game.py             # --- Pydantic models for API request/response bodies
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py       # --- Logic for LangChain, prompts, and LLM calls
│   │   ├── firebase_service.py # --- Reusable client for interacting with Firestore
│   │   └── game_service.py     # --- Core business logic for managing game state
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py          # --- Common utility functions (e.g., random name generator)
│   ├── __init__.py
│   └── main.py                 # --- FastAPI application entrypoint
├── Dockerfile                  # --- To containerize the app for Cloud Run
└── pyproject.toml              # --- Project dependencies and metadata (managed by uv)
```

## 3. Frontend Structure (Vue.js)

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── assets/                 # --- Static assets like CSS, images
│   ├── components/             # --- Reusable UI components (e.g., Button.vue, PlayerCard.vue)
│   ├── router/
│   │   └── index.js            # --- Vue Router configuration (routes for views)
│   ├── services/
│   │   ├── api.js              # --- Central module for making calls to our FastAPI backend
│   │   └── firebase.js         # --- Firebase SDK initialization and config
│   ├── store/
│   │   └── game.js             # --- State management (e.g., Pinia) for the game state
│   ├── utils/
│   │   └── index.js            # --- Common utility functions (e.g., date formatting)
│   ├── views/                  # --- Page-level components
│   │   ├── LobbyView.vue
│   │   ├── GameRoomView.vue
│   │   └── CreateGameView.vue
│   ├── App.vue                 # --- Main Vue application component
│   └── main.js                 # --- Vue app entrypoint
├── index.html
└── package.json
```
