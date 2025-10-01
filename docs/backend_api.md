# Backend API Endpoints

This document provides a detailed specification for the API endpoints exposed by the FastAPI backend server.

## Authentication

All endpoints listed below are protected. The frontend client must include a valid Firebase Auth ID Token in the `Authorization` header of every request, using the `Bearer` scheme. The backend will validate this token on every call to securely identify and authenticate the user.

---

## Game Management

### 1. List Public Games

*   **Endpoint:** `GET /games`
*   **Description:** Fetches a list of all public game rooms that are currently in the `waiting` state and are not yet full.
*   **Why it's needed:** Provides the data for the main lobby screen, allowing players to discover and join ongoing games. Using an API for this (instead of a direct client query) allows for future enhancements like pagination or advanced filtering to be added easily.
*   **Success Response (200 OK):**
    ```json
    [
      {
        "gameId": "game_room_id_1",
        "language": "en",
        "playerCount": 3,
        "maxPlayers": 5
      }
    ]
    ```

### 2. Create Game

*   **Endpoint:** `POST /games`
*   **Description:** Creates a new game room in Firestore with the specified settings. The user making the request is automatically assigned as the host.
*   **Why it's needed:** This is the authoritative entry point for creating a new game. The backend is responsible for correctly initializing the game state in the database.
*   **Request Body:**
    ```json
    {
      "language": "en",
      "aiCount": 1,
      "privacy": "public"
    }
    ```
*   **Success Response (201 Created):**
    ```json
    {
      "gameId": "newly_created_game_room_id"
    }
    ```

### 3. Join Game

*   **Endpoint:** `POST /games/{gameId}/join`
*   **Description:** Adds the authenticated user to the player list of the specified game room.
*   **Why it's needed:** The backend must perform critical validation before allowing a user to join a game, checking if the game exists, if it is still in the `waiting` state, and if it is not already full.
*   **Success Response (200 OK):**
    ```json
    {
      "message": "Successfully joined the game."
    }
    ```

---

## In-Game Actions

### 4. Start Game

*   **Endpoint:** `POST /games/{gameId}/start`
*   **Description:** Transitions the game from the `waiting` state to `in_progress`.
*   **Why it's needed:** This is the primary "Game Master" function and must be handled securely by the backend. It validates that the request comes from the host, checks that the minimum player count has been met, secretly assigns the AI impostor(s), generates the first round's question, and officially starts the game.
*   **Success Response (200 OK):**
    ```json
    {
      "message": "Game started successfully."
    }
    ```

### 5. Cast Vote

*   **Endpoint:** `POST /games/{gameId}/vote`
*   **Description:** Records a vote from the authenticated user for another player during a voting phase.
*   **Why it's needed:** The backend must validate every vote to prevent cheating. It checks if the game is in a `voting` phase, if the user is an active player, and if they have not already voted in the current round. The backend is also responsible for tallying the votes and triggering the elimination logic.
*   **Request Body:**
    ```json
    {
      "votedForId": "uid_of_player_being_voted_for"
    }
    ```
*   **Success Response (204 No Content).**

---

## Player Management

### 6. Leave Game

*   **Endpoint:** `POST /games/{gameId}/leave`
*   **Description:** Allows an authenticated player to gracefully remove themselves from a game room.
*   **Why it's needed:** Handles cases where a player intentionally quits. The backend can then update the game state, removing the player and adjusting the logic accordingly (e.g., checking for win conditions, re-evaluating if all players are ready, etc.). If the host leaves, the backend can enforce a rule to end the game or promote a new host.
*   **Success Response (200 OK):**
    ```json
    {
      "message": "You have successfully left the game."
    }
    ```

### 7. Kick Player (Host-only)

*   **Endpoint:** `POST /games/{gameId}/kick`
*   **Description:** Allows the host of a game to remove another player from the room, typically during the `waiting` phase.
*   **Why it's needed:** A crucial moderation tool for hosts to deal with unresponsive or disruptive players who are preventing a game from starting. The backend must validate that the request is from the game's official host.
*   **Request Body:**
    ```json
    {
      "playerIdToKick": "uid_of_player_to_be_kicked"
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
      "message": "Player successfully kicked."
    }
    ```

### In-Game Orchestration

- **`POST /games/{gameId}/tally-answers`**
  - **Description**: Moves all answers from the hidden `pending_messages` subcollection to the public `messages` log and advances the game. Hosts normally rely on the timer-driven auto-trigger, but this endpoint remains available as a fallback.
  - **Authentication**: Required (Firebase ID Token).
  - **Request Body**: None.
  - **Response**: `204 No Content` on success.

- **`POST /games/{gameId}/tally-votes`**
  - **Description**: Tallies votes, applies eliminations, and transitions to the next round or ends the game. With the new flow, the backend also auto-triggers this endpoint once all human players have voted; the route is kept for manual recovery.
  - **Authentication**: Required (Firebase ID Token).
  - **Request Body**: None.
  - **Response**: `204 No Content` on success.
