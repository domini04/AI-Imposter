# Database Schema & Design

This document outlines the database architecture for the AI Impostor Game, including the roles of different databases, data models, and user management strategies.

## 1. High-Level Summary & Key Decisions

*   **Dual Database Architecture:** The project will use two distinct Google Cloud databases for two different purposes:
    *   **Cloud Firestore:** Serves as the **real-time operational database**. It will manage live game state, active chat logs, and user profiles. Its primary strengths are its real-time data synchronization and flexible, document-based structure.
    *   **Google BigQuery:** Serves as the **analytical data warehouse**. It is an archive for historical data, storing the final results of every game. Its strength is its ability to perform complex analytical queries on massive datasets to track AI performance over time.

*   **User Management Strategy:**
    *   **Initial Approach:** User identity will be managed by **Firebase Anonymous Authentication**. This provides the lowest possible friction for new players, allowing them to join a game instantly by simply choosing a display name.
    *   **Unique Identifier:** Every user (including anonymous ones) is assigned a unique, non-changing User ID (`uid`) by Firebase Authentication. This `uid` will serve as the primary key to link a user's identity to their data across the application (e.g., in Firestore).
    *   **Future-Proofing:** The system is designed to allow for "account upgrading." In the future, an anonymous user can be seamlessly linked to a permanent social login (like Google Sign-In) to save their progress and stats.

*   **Data Flow for Analytics:**
    *   The flow of data from a live game to the analytical warehouse is a one-way, automated process.
    *   1. When a game ends, the FastAPI backend writes a final summary document to a dedicated `game_results` collection in Firestore.
    *   2. A Cloud Function is automatically triggered by this new document.
    *   3. The Cloud Function reads the result data and streams it as a new row into a table in BigQuery, archiving it for analysis.

---

*This document will be updated with detailed collection and table structures as they are finalized.*

## 2. Firestore Data Models

Below are the detailed data structures for our Firestore collections.

---

### `users` Collection

*   **Path:** `/users/{userId}`
    *   The `{userId}` is the unique ID (`uid`) provided by Firebase Authentication.
*   **Purpose:** Stores long-term data associated with a user's session. It is designed to work with anonymous users initially and can be updated if the user creates a permanent account.

```json
// Document for /users/{userId}
{
  "createdAt": "ServerTimestamp", // When the user session was first created
  "isAnonymous": true,            // True for guest accounts, false for permanent ones

  // Fields for future use (will be null/absent for anonymous users)
  "displayName": null,            // A permanent, user-chosen display name
  "photoURL": null,               // A URL to a profile picture from a social login
  "email": null,                  // The user's email if they link their account

  // Stats can be tracked for anonymous users via their persistent session UID
  "stats": {
    "gamesPlayed": 0,
    "impostorIdentified": 0
  }
}
```

---

### `game_rooms` Collection

*   **Path:** `/game_rooms/{gameRoomId}`
    *   The `{gameRoomId}` is a randomly generated unique ID.
*   **Purpose:** Contains the complete real-time state of a single game match.

```json
// Document for /game_rooms/{gameRoomId}
{
  "hostId": "uid_of_the_host_player",
  "status": "waiting", // "waiting", "in_progress", "voting", "finished"
  "language": "en",    // ISO 639-1 code: "en" or "ko"
  "createdAt": "ServerTimestamp",

  // AI Model Selection (Added October 2025)
  "aiModelId": "gpt-5",  // Model identifier from model catalog
                         // Options: "gpt-5", "claude-opus-4.1", "gemini-2.5-pro", "grok-4"
                         // Used by AI service to select LLM provider for AI responses

  "currentRound": 1,
  "rounds": [
    {
      "round": 1,
      "question": "What is your favorite hobby?"
    }
    // New round objects are added here as the game progresses
  ],

  "players": [
    {
      "uid": "persistent_user_uid_1",      // The user's actual UID from Auth
      "gameDisplayName": "Clever Cat",   // The random, per-game nickname
      "isImpostor": false
    },
    {
      "uid": "persistent_user_uid_2",
      "gameDisplayName": "Silent Wolf",
      "isImpostor": true
    }
  ],

  "impostorInfo": {
    "aiModelUsed": "gpt-5",  // Matches aiModelId field (legacy compatibility)
    "aiPlayerId": "persistent_user_uid_2"
  },
  
  "readyPlayerIds": [ // Used to track who is ready for the reveal
    "persistent_user_uid_1"
  ],
  
  "votes": [ // Stores votes for the current round
    {
      "voterId": "persistent_user_uid_1",
      "votedForId": "persistent_user_uid_2"
    }
  ],

  "lastRoundResult": {
    "round": 2,
    "totalVotes": 3,
    "votes": [
      {
        "targetId": "ai_c2ef...",
        "targetName": "Silent Wolf",
        "voteCount": 2,
        "isImpostor": true
      }
    ],
    "eliminatedPlayerId": "ai_c2ef...",
    "eliminatedPlayerName": "Silent Wolf",
    "eliminatedRole": "AI",
    "summary": "Silent Wolf was eliminated (AI).",
    "gameEnded": true,
    "endReason": "AI count now matches or exceeds human count. AI win by parity."
  }
}
```

---

### `pending_messages` Subcollection (New)

*   **Path:** `/game_rooms/{gameRoomId}/pending_messages/{messageId}`
*   **Purpose:** A temporary holding area for messages during a round's "Answer Submission Phase." Messages here are not visible to players. They are moved to the public `messages` subcollection by the backend during the "Simultaneous Reveal."
*   **Structure:** The document structure is identical to the `messages` subcollection.

---

### `messages` Subcollection

*   **Path:** `/game_rooms/{gameRoomId}/messages/{messageId}`
    *   This is a subcollection within each `game_rooms` document.
*   **Purpose:** Stores the chat log for a specific game.

```json
// Document for /game_rooms/{gameRoomId}/messages/{messageId}
{
  "text": "My favorite hobby is hiking.",
  "timestamp": "ServerTimestamp",
  "roundNumber": 1, // The round in which the message was sent
  
  // Denormalized data for performance and historical accuracy
  "senderId": "persistent_user_uid_1",
  "senderName": "Clever Cat" // The in-game name at the time of sending
}
```

## 3. BigQuery Table Schema

This table serves as the analytical data warehouse. It is designed to be denormalized, with one row containing all the relevant information for a single completed game. This structure is optimized for large-scale analytical queries and for exporting data to train AI models.

---

### `game_results` Table

*   **Purpose:** To store a permanent, historical record of every game played.
*   **Ingestion Method:** Data is streamed into this table via a Cloud Function that is triggered by new documents being created in the Firestore `game_results` collection.

#### Table Schema:

| Column Name | Data Type | Mode | Description |
| :--- | :--- | :--- | :--- |
| `gameId` | `STRING` | `REQUIRED` | The unique ID for the game match. |
| `endedAt` | `TIMESTAMP` | `REQUIRED` | The exact time and date the game concluded. |
| `language` | `STRING` | `REQUIRED` | The language the game was played in ('en' or 'ko'). |
| `participants` | `INTEGER` | `REQUIRED` | The number of human players in the game. |
| `aiModelUsed` | `STRING` | `REQUIRED` | The base LLM used (e.g., 'gemini-1.5-pro', 'gpt-4'). |
| `aiModelVersion`| `STRING` | `NULLABLE` | The specific fine-tuned version ID, if applicable. |
| `aiOutcome` | `RECORD` | `REPEATED` | An array of structs detailing the outcome for each AI in the game. |
| `roundData` | `RECORD` | `REPEATED` | An array of structs containing data for each round. |
| `fullChatLog` | `RECORD` | `REPEATED` | An array of structs containing the entire chat transcript. |

#### `aiOutcome` Record Structure (New):

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `aiPlayerId` | `STRING` | The `uid` of the AI player this result pertains to. |
| `result` | `STRING` | The final outcome for this AI ('SURVIVED', 'ELIMINATED'). |
| `eliminatedInRound` | `INTEGER` | The round number the AI was eliminated in. `null` if it survived. |

#### `roundData` Record Structure:

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `roundNumber` | `INTEGER` | The round number (1, 2, 3, etc.). |
| `question` | `STRING` | The question that was asked in this round. |

#### `fullChatLog` Record Structure:

| Field Name | Data Type | Description |
| :--- | :--- | :--- |
| `timestamp` | `TIMESTAMP`| When the message was sent. |
| `roundNumber` | `INTEGER` | The round in which the message was sent. |
| `senderId` | `STRING` | The persistent `uid` of the sender. |
| `senderName` | `STRING` | The in-game random name of the sender. |
| `text` | `STRING` | The content of the chat message. |
