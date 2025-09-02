# Gameplay Rules & Flow

This document defines the specific rules, player experience, and step-by-step flow of the AI Impostor Game.

## 1. Core Game Loop & Principles

The game is a social deduction experience played over a fixed **3-round** structure. The goal for the human players is to identify and eliminate all AI Impostors. The goal for the AI is to survive until the end of the game.

*   **Anonymity:** Players are assigned a new, random nickname for each game.
*   **Language:** Each game is played in a single, pre-selected language (English or Korean).
*   **Simultaneous Reveal:** To eliminate response speed as a clue, all messages within a round's answer phase are revealed to all players at the same time.
*   **Attributed Answers:** Revealed answers are explicitly linked to a player's in-game nickname, which is essential for social deduction.

## 2. Game Flow: Step-by-Step

### 2.1. Pre-Game Lobby

1.  **Lobby View:** Players see a list of available public game rooms, showing details like the language and current player count (e.g., "2/5").
2.  **Game Creation:** A player can host a new game, configuring the following settings:
    *   **Language:** English or Korean.
    *   **Number of AIs:** 1 or 2.
    *   **Rounds:** Fixed at 3.
    *   **Privacy:** Public (listed in the lobby) or Private (join by link only).
3.  **Joining a Room:** Players join a room and wait in a staging area until the host starts the game. A minimum number of players (e.g., 3) is required to start.

### 2.2. Round Flow (Rounds 1, 2, and 3)

Each of the three rounds follows a strict, backend-enforced sequence:

1.  **Question Reveal:** The backend updates the game state with the question for the current round.
2.  **Answer Submission Phase:**
    *   A server-side timer begins (e.g., 3 minutes).
    *   The AI generates its answer(s) immediately, without seeing human responses.
    *   Human players submit their answers via one or more chat messages. These are sent to a hidden, temporary location and are not visible to other players.
3.  **End of Submission Phase:** The phase ends when the **first** of these conditions is met:
    *   The server-side timer expires.
    *   The backend detects that all active players have submitted at least one message.
4.  **Simultaneous Reveal:**
    *   The backend moves all pending messages into the public chat log.
    *   The frontend displays the answers, concatenating each player's messages into a single answer block attributed to their in-game name.

### 2.3. Voting & Elimination Flow (End of Rounds 2 and 3)

1.  **Voting Phase:** After the answers for Round 2 and Round 3 are revealed, a voting period begins.
2.  **Casting Votes:** Each player casts one vote for who they believe is an AI impostor. If there are two AIs, they may have two votes.
3.  **Elimination:** The player with the most votes is eliminated.
4.  **Identity Reveal:** The identity of the eliminated player (Human or AI) is revealed to everyone.

## 3. End Game & Win Conditions

The game ends when one of the following conditions is met:

*   **Human Victory:** All AI impostors have been successfully voted out and eliminated.
*   **AI Victory:** At least one AI impostor survives the final vote at the end of Round 3.
