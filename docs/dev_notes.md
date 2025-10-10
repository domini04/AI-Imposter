This document serves as an architectural decision record (ADR). Its purpose is to document key technical decisions, architectural changes, and the reasoning behind them. It is not a log of tasks completed, but a record of significant choices that shape the project's design and future development.

## Development Decision Records

### **September 1, 2024 - Hybrid Database Strategy**

**Issue**: The project requires two distinct types of data handling: low-latency, real-time updates for active game state and large-scale, analytical queries for historical data to be used in AI training. A single database technology is often not optimal for both use cases.

**Decision**: We will use a hybrid database model. Google Cloud Firestore will be used for all real-time data, including game rooms, player lists, and live chat. Google BigQuery will be used as a data warehouse for storing historical game results and analytics.

**Reasoning**: This approach uses the right tool for the job. Firestore's real-time synchronization capabilities are ideal for the interactive gameplay loop. BigQuery is a columnar data warehouse designed for the complex, large-scale analytical queries we will need to perform to extract training data and monitor AI performance, a task for which Firestore is not suited.

### **September 1, 2024 - Frictionless User Authentication**

**Issue**: The MVP of the game should allow players to join and play as quickly as possible, without the friction of a traditional email/password sign-up process. However, the backend still requires a secure and unique identifier for each player.

**Decision**: We will use Firebase Anonymous Authentication for the initial version of the game. This creates a temporary, unique user account for each player session without requiring any credentials.

**Reasoning**: This strategy provides the best of both worlds for an MVP. It offers a frictionless "guest" experience for the user while still providing the backend with a secure, unique UID for each player. This UID is essential for tracking players within a game and for authentication with our backend API. The complexity of full user accounts (social logins, password recovery) is deferred, allowing us to focus on core gameplay features first.

### **September 3, 2024 - Layered Backend Architecture**

**Issue**: We needed a backend structure that was maintainable, testable, and scalable. A monolithic approach where HTTP handling and business logic are mixed would quickly become difficult to manage.

**Decision**: The backend is structured into two primary layers: an API Layer (in `app/api/endpoints/`) and a Service Layer (in `app/services/`). The API layer is responsible only for handling HTTP requests and responses, while the Service layer contains all the core business logic, independent of the web.

**Reasoning**: This layered architecture promotes a strong separation of concerns. It makes the business logic highly reusable and, most importantly, allows for isolated unit testing of the core game rules without the overhead of a web server. This leads to a more robust, maintainable, and scalable codebase.

### **September 5, 2024 - Granular In-Game State Management**

**Issue**: The existing `status` field in the `game_rooms` document (with values like "waiting", "in_progress") is too broad to manage the distinct phases within an active game round. It doesn't provide a mechanism to enforce rules like preventing votes during the answer submission phase.

**Decision**: We will introduce a new field, `roundPhase`, to the `game_rooms` document. This field will hold specific string values representing the current state of a round, such as `ANSWER_SUBMISSION`, `VOTING`, and `ROUND_ENDED`. The backend will be solely responsible for transitioning this state.

**Reasoning**: A granular `roundPhase` field establishes an authoritative state machine for the game flow. It allows the backend to validate player actions against the current phase, preventing invalid operations and ensuring the game progresses according to the rules. This separation of concerns makes the core game logic more robust, easier to test, and less prone to race conditions or client-side manipulation.

### **September 5, 2024 - Handling Time-Based State Transitions**

**Issue**: Our game requires server-authoritative state transitions to occur after a set time (e.g., ending the answer submission phase after 3 minutes). However, stateless web servers like FastAPI cannot natively "wait" or schedule future actions, presenting a challenge for managing the game's lifecycle automatically.

**Decision**: For the MVP, we will adopt a "Client-Triggered, Server-Validated" approach.
1.  When a timed phase begins, the backend will write a definitive `roundEndTime` timestamp to the Firestore document.
2.  The frontend will use this timestamp to display a countdown.
3.  When the timer expires, the client will send a request to a dedicated endpoint (e.g., `/tally-answers`).
4.  The backend will then validate this request by comparing the current server time to the stored `roundEndTime` before executing the state transition, ensuring the action is legitimate.

**Reasoning**: This decision was made after considering two options: the chosen approach and a more complex, production-grade solution using serverless scheduled jobs (e.g., Google Cloud Tasks and Cloud Functions). While the serverless approach offers guaranteed execution independent of client activity, it introduces significant infrastructural and local development complexity. The chosen client-triggered method maintains server authority (by validating the timestamp) and is far simpler to implement for an MVP, requiring no additional cloud services. The acceptable trade-off is that the game state will not advance if all players disconnect, which is a minor risk for the initial version of the game.

### **September 26, 2025 - Frontend State & Real-time Data Architecture**

**Issue**: The frontend requires a robust architecture to manage shared application state (like the current game data) and handle real-time, bi-directional data flow with Firestore without coupling the UI components directly to the data services.

**Decision**: We will adopt a two-part architecture for frontend data management:
1.  **Centralized State Management**: We will use **Pinia** as the official state management library. A central `useGameStore` will be the single source of truth for all shared state. All backend API calls will be orchestrated through Pinia actions, which call our `api.js` service.
2.  **Dedicated Listener Service**: We will create a dedicated `services/game_listener.js` module. This service will be the only part of the application responsible for managing the real-time `onSnapshot` subscription to Firestore. It will push live data into the Pinia store via a store action, but will not interact with UI components directly.

**Reasoning**: This layered approach creates a clean, one-way data flow (`Firestore -> Listener Service -> Pinia Store -> UI Components`) and a clear separation of concerns.
*   **Pinia** provides a predictable, centralized container for our state, simplifying debugging and making our components purely presentational.
*   The **dedicated listener service** encapsulates the complexity of managing real-time subscriptions. This prevents memory leaks by ensuring subscriptions are properly handled during the component lifecycle (`onMounted`/`onUnmounted`) and keeps our UI components decoupled from the Firebase SDK, making the codebase more modular and maintainable.

### **September 26, 2025 - Simultaneous Nickname Reveal Strategy**

**Issue**: An information leak was identified in the game's pre-start phase. Human players were assigned a nickname upon joining the lobby, while the AI player was only assigned a name when the game officially started. This would allow human players to easily identify the AI by simply seeing which new player appeared at the start of the match, undermining the core social deduction mechanic.

**Decision**: We will implement a "Simultaneous Nickname Reveal" strategy to close this exploit, involving both backend and frontend changes:
1.  **Backend Logic**: The backend service will be modified to **not** assign any `gameDisplayName` when a human player joins a game. Instead, the "Start Game" function will be solely responsible for generating and assigning unique, random nicknames to *all* participants (human and AI) in a single, atomic operation at the moment the game's status transitions to `in_progress`.
2.  **Frontend UI**: The `PlayerList.vue` component will be made state-aware. While the game `status` is "waiting," it will display generic, anonymous labels (e.g., "Player 1," "Player 2"). Once the game starts and the real nicknames are populated by the backend, the component will then display the `gameDisplayName` for all players.

**Reasoning**: This approach completely eliminates the information leak and prevents meta-gaming. It ensures all players start on an equal footing and adds a moment of reveal when the game begins, enhancing the user experience. By making the backend the single source of truth for the simultaneous assignment, we guarantee fairness and consistency.

### **October 1, 2025 - Automatic Voting Completion & Round Summaries**

**Issue**: Voting phases required manual tally triggers and provided no structured explanation of results. Players could finish voting, but the game would not automatically advance, and the UI could not explain who was eliminated or why the game ended.

**Decision**: The backend now auto-tallies once every active human has cast a vote and persists a `lastRoundResult` summary (vote counts, eliminated player, role, end reason) on the game document. The frontend consumes that summary to display detailed phase messaging and end-of-game explanations.

**Reasoning**: This approach keeps the flow authoritative and removes race conditions, while giving players clear closure on each round. Persisted summaries also lay the groundwork for analytics and replay features without additional queries.
