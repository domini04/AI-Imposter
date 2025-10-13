# MVP Implementation Plan

This document provides a granular, step-by-step checklist for developing the Minimum Viable Product (MVP) of the AI Impostor Game, as defined in Phase 1 of the `development_process.md`.

## 1. Initial Setup & Configuration

- [x] **Project Structure:** Create the monorepo folder structure (`/frontend`, `/backend`, etc.) as defined in `project_structure.md`.
- [x] **Backend Environment:** In the `/backend` directory, initialize a new project with `uv`. Create the `pyproject.toml` file.
- [x] **Frontend Environment:** In the `/frontend` directory, initialize a new Vue.js 3 project.
- [x] **Version Control:** Initialize a Git repository in the root directory and create the initial commit.
- [x] **GCP/Firebase Project:**
    - [x] Create a new project in the Google Cloud Console.
    - [x] In the Firebase console, create a new project linked to the GCP project.
    - [x] Enable the following services: Authentication (with Anonymous sign-in method), Firestore, and Cloud Run.

## 2. Backend Development (FastAPI)

### 2.1. Boilerplate & Configuration
- [x] **FastAPI App:** Create the main FastAPI app entrypoint in `backend/app/main.py`.
- [x] **CORS Middleware:** Configure CORS to allow requests from the frontend's development server.
- [x] **Firebase Admin SDK:** Create `firebase_service.py` and implement the logic to initialize the Firebase Admin SDK using a service account.

### 2.2. Core API Endpoints & Logic
- [x] **Pydantic Models:** In `backend/app/models/`, define all Pydantic models for API request and response bodies.
- [x] **Auth Dependency:** In `backend/app/api/deps.py`, create a reusable dependency to decode and validate the Firebase Auth ID Token from the `Authorization` header.
- [x] **Endpoint: `POST /games`:** Implement the "Create Game" endpoint.
- [x] **Endpoint: `GET /games`:** Implement the "List Public Games" endpoint.
- [x] **Endpoint: `POST /games/{id}/join`:** Implement the "Join Game" endpoint.
- [x] **Endpoint: `POST /games/{id}/start`:** Implement the "Start Game" endpoint, including the logic for secret impostor assignment.
- [x] **Endpoint: `POST /games/{id}/submit-answer`:** Implement the logic to handle a player submitting their answer.
- [x] **Endpoint: `POST /games/{id}/vote`:** Implement the logic for casting a vote.

### 2.3. AI Service Implementation (Phase 1 Complete)
- [x] **AI Service Module:** Create `ai_service.py` with LangChain integration.
- [x] **OpenAI Provider:** Implement GPT-5 provider factory with configuration.
- [x] **Prompt Engineering:** Design and implement English system/user prompts.
- [x] **Conversation History:** Implement history extraction and formatting from Firestore.
- [x] **LCEL Chain:** Build LangChain Expression Language chain (prompt | llm | parser).
- [x] **Public Interface:** Create `generate_ai_response()` function with error handling.
- [x] **Game Integration:** Update `game_service.py` to call AI service for AI players.
- [x] **Testing:** Create and run integration tests with real GPT-5 API calls.
- [x] **Issue Resolution:** Resolve GPT-5 max_tokens compatibility issue.
- [ ] **Multi-Provider Support:** Add Anthropic, Google, xAI providers (Phase 2).
- [ ] **Korean Language:** Implement Korean prompt templates (Phase 3).
- [ ] **Production Hardening:** Add retry logic, structured logging, monitoring (Phase 4).

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

## 4. Deployment Setup
- [ ] **Dockerfile:** Create the `Dockerfile` for containerizing the FastAPI application.
- [ ] **Initial Deployment:** Write a script or document the steps to build the Docker image and deploy it to Cloud Run for the first time.

## 5. First Playable Milestone

- [ ] **End-to-End Test:** Manually test the full game loop:
    1. A user can create a game.
    2. Other users can see and join the game.
    3. The host can start the game.
    4. Players can submit answers, which are then revealed.
    5. A full, playable game can be completed.

## 6. AI Performance Analytics Pipeline

- [ ] **Backend Logic:** Implement the logic in the `game_service` to write a final summary document to the `game_results` collection in Firestore when a game concludes.
- [ ] **BigQuery Setup:** Create the `game_results` table in Google BigQuery with the schema from `database_schema.md`.
- [ ] **Data Ingestion Function:** Write and deploy a Cloud Function that is triggered by new documents in the Firestore `game_results` collection and streams the data into BigQuery.
- [ ] **Performance Dashboard:** Connect Looker Studio to the BigQuery table and build a basic dashboard to visualize key metrics like AI survival rate.

## 7. Asynchronous Training Pipeline

- [ ] **Data Extraction Function:** Create a scheduled Cloud Function that queries BigQuery for data from successful games.
- [ ] **Data Formatting:** Implement logic within the function to format the query results into a structured training dataset (e.g., JSONL).
- [ ] **Cloud Storage:** Configure a Cloud Storage bucket to receive the formatted training datasets.
- [ ] **Training Orchestration:** Set up a Vertex AI Pipeline (or Cloud Workflow) that is triggered when a new dataset is uploaded to Cloud Storage.
- [ ] **Fine-Tuning Integration (PoC):** Configure the pipeline to call the fine-tuning API for a single provider (e.g., Vertex AI) as a proof of concept.
- [ ] **Model Management:** Implement a strategy for versioning the fine-tuned models so they can be referenced by the main application.
