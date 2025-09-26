# Game Room: Frontend Implementation Plan

This document outlines the architecture, components, and data flow for the `GameRoomView` of the AI Impostor Game.

## 1. High-Level Architecture

The `GameRoomView` is a "smart" container component. It is responsible for orchestrating several smaller, "dumb" presentational sub-components. Its primary data source is the `currentGame` object from the `useGameStore` (Pinia), which is kept in sync with the Firestore database in real-time.

### Interaction Diagram

```mermaid
graph TD
    subgraph "External Services"
        A[Firestore Real-time Listener]
        B[Pinia Store (useGameStore)]
    end

    subgraph "GameRoomView.vue (Smart Container)"
        C[GameRoomView]
    end

    subgraph "UI Sub-Components (Dumb)"
        D[GameStatusDisplay]
        E[PlayerList]
        F[ChatDisplay]
        G[MessageInput]
        H[VotingInterface]
        I[HostControls]
    end

    A -- "1. Pushes live data" --> B;
    B -- "2. Provides reactive state" --> C;
    C -- "3. Passes props down" --> D;
    C -- "3. Passes props down" --> E;
    C -- "3. Passes props down" --> F;
    C -- "Conditionally renders" --> G;
    C -- "Conditionally renders" --> H;
    C -- "Conditionally renders" --> I;

    G -- "4. Emits 'send-message' event" --> C;
    H -- "4. Emits 'cast-vote' event" --> C;
    I -- "4. Emits 'start-game' event" --> C;
    C -- "5. Calls store action" --> B;
```

## 2. Component Breakdown

The Game Room is divided into six key functional parts, each with its own dedicated component.

| Part                    | Component Name            | Role & Characteristics                                                                                                                                                             |
| ----------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Game & Round Status** | `GameStatusDisplay.vue`   | A simple, read-only component that receives props (`currentRound`, `question`) and displays them.                                                                                  |
| **Player Roster**       | `PlayerList.vue`          | Renders the list of participants. It receives the `players` array as a prop and uses a `v-for` loop to render a `PlayerCard.vue` for each player.                                     |
| **Chat & Messages**     | `ChatDisplay.vue`         | Displays the official game chat log. It receives the `messages` array as a prop and is responsible for formatting them for readability.                                              |
| **User Input**          | `MessageInput.vue`        | A form for submitting answers. It is conditionally rendered during the `ANSWER_SUBMISSION` phase and writes directly to a hidden Firestore subcollection.                              |
| **Voting**              | `VotingInterface.vue`     | An interface for players to vote. It is conditionally rendered during the `VOTING` phase, receives active players as a prop, and emits a `cast-vote` event with the selected user's ID. |
| **Host Actions**        | `HostControls.vue`        | A set of controls visible only to the host. It is conditionally rendered and emits a `start-game` event when the host initiates the game.                                           |

## 3. Firebase Real-Time Integration

The core of the Game Room is its real-time data synchronization with Firestore. This interaction is managed by a dedicated service to maintain a clean separation of concerns.

**Data Read Flow:** `Firestore -> game_listener.js -> Pinia Store -> Vue Components`

1.  **`services/game_listener.js` (The Subscriber)**: This module is responsible for all direct communication with Firestore. It uses the `onSnapshot` method to listen for changes to the game document in real-time. When data changes, it calls an action in the Pinia store.
2.  **`useGameStore` (The State Synchronizer)**: The store's `setCurrentGame(gameData)` action receives live data from the listener. Because Pinia's state is reactive, any component using this state will automatically update.
3.  **`GameRoomView.vue` (The Conductor)**: This component manages the subscription's lifecycle. It calls `subscribeToGame()` when it's mounted and `unsubscribeFromGame()` when it's unmounted to prevent memory leaks.

**Data Write Exception (`MessageInput.vue`)**: To handle the simultaneous reveal of answers, the `MessageInput` component writes messages to a hidden `pending_messages` subcollection in Firestore via a dedicated `chat_service.js`.

## 4. Backend API Integration

Authoritative, state-changing actions are handled by our secure FastAPI backend. The interaction is always indirect, flowing from the UI component to the Pinia store, which then calls the `api.js` service.

**Action Flow:** `UI Component -> GameRoomView -> Pinia Store Action -> api.js Service -> Backend`

-   **`HostControls.vue` -> `startGame()`**: When the host clicks "Start Game," the event is propagated up to the `GameRoomView`, which calls the `startGame` action in the store. The store then makes an authenticated API call to the `POST /games/{gameId}/start` endpoint.
-   **`VotingInterface.vue` -> `castVote()`**: When a player votes, the event (with the `votedForId`) is sent to the `GameRoomView`, which calls the `castVote` action. The store then makes an authenticated API call to the `POST /games/{gameId}/vote` endpoint.

This architecture ensures a robust, scalable, and maintainable implementation of the Game Room.
