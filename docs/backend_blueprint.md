# Backend Blueprint

This document outlines the architecture and responsibilities of the custom backend server for the AI Impostor Game.

## 1. Core Technology

*   **Framework:** **FastAPI**
*   **Deployment Environment:** **Cloud Run** (Containerized)

The backend will serve as a stateless API, leveraging Firebase Firestore for real-time data persistence and state management.

## 2. API Endpoint Specification

For a detailed breakdown of the specific API endpoints, request/response formats, and authentication requirements, please refer to the following document:

*   [**Backend API Endpoints**](./backend_api.md)

## 3. Key Responsibilities

The backend acts as the secure and authoritative "Game Master" and "AI Handler." While Firebase manages user sessions and the real-time data layer, the FastAPI server handles all actions requiring security, authority, and complex, stateful logic.

### 3.1. Authoritative Game State Management

The backend is the ultimate source of truth for the game's rules and progression. It prevents cheating and ensures the game flows correctly.

*   **Game Lifecycle:** Manages the creation of game rooms, the official start of the game, the progression between rounds, and the final determination of the winner.
*   **Player Actions:** Validates all critical player actions (e.g., voting) to ensure they are performed at the correct time and according to the rules.
*   **State Transitions:** Executes all major state changes by updating the `game_rooms` document in Firestore (e.g., changing `status` from `waiting` to `in_progress`).

### 3.2. AI Orchestration Engine

The backend is responsible for all aspects of the AI's participation in the game.

*   **AI Assignment:** At the start of a game, the backend secretly assigns one of the players to be the AI impostor. This information is stored server-side and is not exposed to the client.
*   **Prompt Engineering & Management:** The backend will use a framework like **LangChain** to manage a library of prompt templates. This allows for sophisticated and version-controlled prompting strategies.
*   **Context-Aware Generation:** When it is the AI's turn, the backend gathers the necessary context (game language, current question, recent chat history) from Firestore to build a rich, dynamic prompt.
*   **Secure LLM API Calls:** The backend securely stores and uses the API keys for all LLM providers (Google, OpenAI, Anthropic). It makes server-to-server calls to the selected LLM and posts the response back to the `messages` subcollection in Firestore on behalf of the AI player.

## 4. Security Scope

For this project, the security focus is pragmatic, addressing critical vulnerabilities without over-engineering for a full production service.

1.  **API Key Protection (Critical):** All LLM provider API keys will be stored and used exclusively on the backend server. They will never be exposed to the client-side application.
2.  **Game Logic Integrity (Critical):** The backend will serve as the authoritative rule enforcer. All state-changing actions (starting a game, casting a vote, etc.) will be validated on the server to prevent cheating.
3.  **Data Access Control (Via Firestore):** Unauthorized database manipulation will be prevented using Firestore Security Rules. These rules will enforce policies such as ensuring a user can only write messages to a game they are a legitimate participant in.
