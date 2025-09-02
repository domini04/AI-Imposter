# AI Impostor Game: Step-by-Step Development Process

This document outlines a phased approach to developing the AI Impostor Game, based on our detailed design blueprints. The process is designed to deliver a functional core product (MVP) quickly and then iteratively add more advanced features.

---

### Phase 1: Foundation & Core Gameplay Loop (MVP)

**Goal:** To build a functional, playable version of the game with the core mechanics defined in our design documents.

1.  **Project & Environment Setup:**
    *   Create the monorepo structure as defined in `project_structure.md`.
    *   Initialize the `uv`-managed Python environment for the backend.
    *   Initialize the Vue.js project for the frontend.
    *   Set up the Google Cloud & Firebase project and enable all required services (Authentication, Firestore, Cloud Run).

2.  **Backend Implementation (FastAPI):**
    *   Develop the FastAPI application boilerplate and server configuration.
    *   Implement the core "Game Master" API endpoints required for the MVP: `POST /games`, `GET /games`, `POST /games/{id}/join`, and `POST /games/{id}/start`.
    *   Implement the business logic in the service layer to manage the game state in Firestore according to our defined rules.
    *   Containerize the application with a `Dockerfile`.

3.  **Frontend Implementation (Vue.js):**
    *   Develop the main views: `LobbyView`, `CreateGameView`, and the initial `GameRoomView`.
    *   Implement Firebase Anonymous Authentication on application startup.
    *   Create services to connect to both the Firebase SDK and our backend API.
    *   Implement the UI components for displaying game lists, creating a game, and joining a game.
    *   Set up a real-time listener in the `GameRoomView` to sync with the Firestore game state.

4.  **Initial AI Integration:**
    *   In the backend, create an `ai_service` that uses **LangChain** to manage prompts.
    *   Integrate a client for a single LLM provider.
    *   Implement the logic that is triggered when it's the AI's turn, generates an answer, and posts it to the `pending_messages` subcollection.

5.  **Core Gameplay Loop:**
    *   Implement the "Simultaneous Reveal" logic, including the `POST /games/{id}/submit-answer` endpoint and the backend logic to handle it.
    *   Implement the voting and elimination flow, including the `POST /games/{id}/vote` endpoint.
    *   Connect all frontend components to the backend API and Firebase to create a playable, end-to-end game loop.

---

### Phase 2: Analytics & Performance Tracking

**Goal:** To establish the data pipeline that captures game results for analysis and future model training.

1.  **Game Outcome Logic:**
    *   Implement the backend logic to determine the game's final outcome based on the win conditions.
    *   When a game ends, the backend will write a final summary document to the `game_results` collection in Firestore.

2.  **Data Ingestion to BigQuery:**
    *   Set up the `game_results` table in Google BigQuery with the schema defined in `database_schema.md`.
    *   Write and deploy the Cloud Function that triggers on new documents in the `game_results` collection and streams the data into the BigQuery table.

3.  **Performance Dashboard:**
    *   Connect Looker Studio to the BigQuery table.
    *   Build an initial dashboard to visualize key metrics, such as the AI's survival rate per round.

---

### Phase 3: Asynchronous Training Pipeline

**Goal:** To automate the process of fine-tuning the AI models based on game data.

1.  **Data Extraction & Preparation:**
    *   Create a process (e.g., a scheduled Cloud Function) that queries **BigQuery** for successful games (`aiOutcome.result = 'SURVIVED'`).
    *   This process will format the query results into a structured training dataset (e.g., JSONL) and upload it to a Cloud Storage bucket, sorted by language and model.

2.  **Training Orchestration:**
    *   Set up a **Vertex AI Pipeline** or **Cloud Workflow** to orchestrate the fine-tuning process.
    *   This workflow will be triggered when a new dataset is uploaded to Cloud Storage.

3.  **Model Fine-Tuning & Deployment:**
    *   The pipeline will call the appropriate fine-tuning API for the given model.
    *   After a successful job, the pipeline will register the new model version and automatically deploy it, completing the learning loop.

---

### Phase 4 & 5: Multi-LLM Integration, Polish & Production Readiness

These phases remain as previously defined, focusing on expanding the platform to support multiple LLM providers, refining the UI/UX, hardening security, and establishing robust CI/CD pipelines.
