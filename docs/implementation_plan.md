# MVP Implementation Plan

This document provides a granular, step-by-step checklist for developing the Minimum Viable Product (MVP) of the AI Impostor Game, as defined in Phase 1 of the `development_process.md`.

## 1. Initial Setup & Configuration

- [x] **Project Structure:** Create the monorepo folder structure (`/frontend`, `/backend`, etc.) as defined in `project_structure.md`.
- [x] **Backend Environment:** In the `/backend` directory, initialize a new project with `uv`. Create the `pyproject.toml` file.
- [x] **Frontend Environment:** In the `/frontend` directory, initialize a new Vue.js 3 project.
- [ ] **Version Control:** Initialize a Git repository in the root directory and create the initial commit.
- [ ] **GCP/Firebase Project:**
    - [ ] Create a new project in the Google Cloud Console.
    - [ ] In the Firebase console, create a new project linked to the GCP project.
    - [ ] Enable the following services: Authentication (with Anonymous sign-in method), Firestore, and Cloud Run.

## 2. Backend Development (FastAPI)

### 2.1. Boilerplate & Configuration
- [x] **FastAPI App:** Create the main FastAPI app entrypoint in `backend/app/main.py`.
- [x] **CORS Middleware:** Configure CORS to allow requests from the frontend's development server.
- [x] **Firebase Admin SDK:** Create `firebase_service.py` and implement the logic to initialize the Firebase Admin SDK using a service account.

### 2.2. Core API Endpoints & Logic
- [ ] **Pydantic Models:** In `backend/app/models/`, define all Pydantic models for API request and response bodies.
- [ ] **Auth Dependency:** In `backend/app/api/deps.py`, create a reusable dependency to decode and validate the Firebase Auth ID Token from the `Authorization` header.
- [ ] **Endpoint: `POST /games`:** Implement the "Create Game" endpoint.
- [ ] **Endpoint: `GET /games`:** Implement the "List Public Games" endpoint.
- [ ] **Endpoint: `POST /games/{id}/join`:** Implement the "Join Game" endpoint.
- [ ] **Endpoint: `POST /games/{id}/start`:** Implement the "Start Game" endpoint, including the logic for secret impostor assignment.
- [ ] **Endpoint: `POST /games/{id}/submit-answer`:** Implement the logic to handle a player submitting their answer.
- [ ] **Endpoint: `POST /games/{id}/vote`:** Implement the logic for casting a vote.

### 2.3. Deployment Setup
- [ ] **Dockerfile:** Create the `Dockerfile` for containerizing the FastAPI application.
- [ ] **Initial Deployment:** Write a script or document the steps to build the Docker image and deploy it to Cloud Run for the first time.

## 3. Frontend Development (Vue.js)

### 3.1. Boilerplate & Configuration
- [ ] **Firebase SDK:** Create `frontend/src/services/firebase.js` to initialize the client-side Firebase SDK.
- [ ] **Anonymous Auth:** Implement the logic to automatically sign the user in anonymously when the app first loads.
- [ ] **Vue Router:** Set up routes for the `LobbyView`, `CreateGameView`, and `GameRoomView`.
- [ ] **API Service:** Create `frontend/src/services/api.js`, a centralized module for making authenticated requests to our backend API.
- [ ] **State Management:** Set up a Pinia store to manage global UI state and the current game state.

### 3.2. Views & Components
- [ ] **View: `LobbyView.vue`:**
    - [ ] Build the UI to display a list of public games.
    - [ ] Implement the "Refresh" button functionality.
    - [ ] Implement the "Join Game" functionality.
- [ ] **View: `CreateGameView.vue` (or Modal):**
    - [ ] Build the form for game creation.
    - [ ] Connect the form to the `POST /games` backend endpoint.
- [ ] **View: `GameRoomView.vue`:**
    - [ ] Set up the real-time Firestore listener for the current game room document.
    - [ ] Display the current round, question, and player list from the Firestore data.
    - [ ] Implement the message input component.
    - [ ] Implement the logic to write messages to the `pending_messages` subcollection.
    - [ ] Implement the UI to display the revealed chat log from the public `messages` subcollection.
    - [ ] Implement the voting interface.
    - [ ] Connect the "Submit Answer" and "Cast Vote" actions to their respective backend endpoints.

## 4. First Playable Milestone

- [ ] **End-to-End Test:** Manually test the full game loop:
    1. A user can create a game.
    2. Other users can see and join the game.
    3. The host can start the game.
    4. Players can submit answers, which are then revealed.
    5. A full, playable game can be completed.
