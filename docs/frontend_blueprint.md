# Frontend Blueprint

This document outlines the architecture, technology stack, and component breakdown for the front-end application of the AI Impostor Game.

## 1. Core Technology & Architecture

*   **Framework:** **Vue.js** (Version 3, using the Composition API).
*   **Architecture:** **Single Page Application (SPA)**. The application will be a client-side rendered SPA responsible for all UI and real-time data interactions.
*   **Data Layer:** The front-end will communicate with two backend services:
    1.  **Firebase:** Using the Firebase SDK, the app will connect directly to Firestore for real-time data synchronization (game state, chat) and to Firebase Authentication for user session management.
    2.  **FastAPI Backend:** Using standard HTTP requests (e.g., via `fetch` or `axios`), the app will call our custom backend API for authoritative game logic actions (e.g., creating a game, starting a game, casting a vote).

## 2. Key Views & Components

The application will be broken down into several key views.

### 2.1. The Lobby

*   **Purpose:** The main entry point for players.
*   **Key Components:**
    *   **Public Games List:** Displays a list of available games with public visibility. Each item will show the game's language, player count (e.g., "3/5"), and current status.
    *   **Refresh Button:** A button to manually refresh the list of public games.
    *   **Create Game Button:** Opens a modal or navigates to a new view for creating a game.
    *   **Join by Link/Code:** An input field to allow a player to join a private game.

### 2.2. Game Creation View

*   **Purpose:** A simple form for a host to configure a new game.
*   **Key Components:**
    *   **Settings Form:** Allows the host to configure:
        *   Language (English/Korean)
        *   Number of AIs (1-2)
        *   Privacy (Public/Private)
    *   **Generate Game Button:** Creates the game via an API call to the backend and navigates the host to the Game Room view.

### 2.3. Game Room / Main Game View

*   **Purpose:** The central hub where the game is played. This is the most complex view.
*   **Key Components:**
    *   **Game State Display:** Shows the current round number, the question for the round, and the remaining time in the answer submission phase.
    *   **Player List:** Displays the list of current players with their random in-game nicknames. Can also be used to show which players have been eliminated.
    *   **Chat Display Area:** The main area where revealed messages are displayed. It will concatenate multiple messages from a single user in a round into a single, cohesive block.
    *   **Message Input Area:** The text box and send button for players to submit their answers during the submission phase. This component will be disabled outside of the submission phase.
    *   **Voting Interface:** During the voting phase, this component will appear, allowing the player to select a user to vote for.
    *   **Game Over Screen:** A modal or view to announce the game's outcome, revealing the impostor(s) and who won.
