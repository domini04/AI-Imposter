# Project Blueprint: AI Impostor Game

- **Last Updated:** August 29, 2025
- **Project Lead:** AI Software Engineer

## Detailed Design Documents

For specific, in-depth design details, please refer to the following documents:
*   [**Gameplay Rules & Flow**](./gameplay_rules.md)
*   [**Database Schema & Design**](./database_schema.md)
*   [**Frontend Blueprint**](./frontend_blueprint.md)
*   [**Backend Blueprint**](./backend_blueprint.md)

## 1. Project Overview & Goals

### 1.1. Core Concept
This project is a multiplayer, chat-based social deduction game. A small group of human players (e.g., ~5) enter a game room and are joined by one or more AI agents disguised as human players. The game proceeds in turns, with a topic or question presented to the group. The primary goal for the human players is to correctly identify the AI impostor(s). The AI's goal is to remain undetected.

### 1.2. Key Objectives
- **Feasibility:** Develop a functional prototype with a simple, messenger-like interface.
- **Multi-LLM Integration:** Utilize multiple LLM APIs (e.g., from Google, Anthropic, OpenAI) to create a variety of AI agents.
- **Automated Learning:** Create an automated pipeline to log game conversations and use this data to continuously fine-tune each AI model independently.
- **Performance Tracking:** Implement a system to track, monitor, and visualize the performance of each AI model separately, allowing for direct comparison.
- **Scalability & Cost:** The preferred architecture is serverless, ensuring it is cost-effective and can scale with traffic.

## 2. Core Architecture Blueprint (GCP & Firebase)
The system is designed to be provider-agnostic where possible, with three distinct, decoupled components: the live game service, the background AI training pipeline, and the performance analytics pipeline.

### 2.1. Real-time Game Service
This component handles all live player interactions and gameplay logic.
- **Frontend:** A Vue.js Single Page Application responsible for all UI rendering and client-side interactions.
- **Backend Server:** A containerized FastAPI application that acts as the authoritative "Game Master," manages game logic, and orchestrates all AI responses.
- **User Management & Database:** Firebase Authentication and Cloud Firestore provide user session management and the real-time database layer for live game state and chat.

### 2.2. Asynchronous Training Pipeline
This automated workflow runs independently to continuously improve each AI model.
- **AI Fine-Tuning & Management:** A central orchestrator (e.g., Cloud Workflows or Vertex AI Pipelines) automates the fine-tuning jobs on their respective platforms (e.g., Vertex AI for Gemini models, OpenAI's API for GPT models). The resulting improved models are versioned and deployed, completing the learning loop for each provider.

### 2.3. AI Performance Analytics Pipeline
This component captures and analyzes game results to track the AI's long-term performance.
- **Data Ingestion:** An event-driven pipeline streams final game results from Firestore into a data warehouse.
- **Data Warehouse:** Google BigQuery is used as the analytical data warehouse to store the historical record of all game outcomes.
- **Visualization:** A Looker Studio dashboard connected to BigQuery provides performance monitoring and comparison across different LLMs.

## 3. Architecture Diagram(Rough Draft)
This diagram illustrates the flow of data across all three components of the system.

```mermaid
graph TD
    subgraph " "
        direction LR
        subgraph "Real-time Gameplay Loop"
            direction TB
            A[<font size=5><b>Player's Browser</b></font><br>React/Vue App] -->|HTTPS| B(<b>Firebase Hosting</b>);
            A -->|Login/Auth| C(<b>Firebase Authentication</b>);
            A <-->|Live Chat Sync| D(<b>Cloud Firestore</b><br><i>chat_logs</i> collection);
            E(<b>Cloud Run</b><br>FastAPI Backend) -->|Writes AI Response| D;
            E -->|Reads History/Context| D;
            E -->|<b>Writes Final Outcome</b>| D_Results(<b>Cloud Firestore</b><br><i>game_results</i> collection);
            style E fill:#4285F4,color:#fff;

            subgraph "LLM Providers"
                F_GCP(<b>Vertex AI</b>);
                F_OpenAI(<b>OpenAI API</b>);
                F_Anthropic(<b>Claude API</b>);
            end

            E -->|Sends Prompt| F_GCP;
            E -->|Sends Prompt| F_OpenAI;
            E -->|Sends Prompt| F_Anthropic;

            F_GCP -->|Sends Response| E;
            F_OpenAI -->|Sends Response| E;
            F_Anthropic -->|Sends Response| E;

            style F_GCP fill:#34A853,color:#fff;
            style F_OpenAI fill:#10A37F,color:#fff;
            style F_Anthropic fill:#D97757,color:#fff;
        end

        subgraph "Asynchronous Loops"
            direction TB
            subgraph "Training Pipeline"
                G(<b>Cloud Scheduler</b>) -->|Triggers| H(<b>Cloud Function</b><br>Extracts & Formats Data);
                style G fill:#FBBC05,color:#333;
                H -->|Reads Chat Logs| D;
                H -->|Writes Dataset| I(<b>Cloud Storage</b><br><i>Datasets sorted by LLM</i>);
                I -->|Triggers| J(<b>Cloud Workflows /<br>Vertex AI Pipelines</b><br><i>Training Orchestrator</i>);
                
                subgraph "Provider-Specific Fine-Tuning"
                    K_GCP(<b>Vertex AI<br>Fine-Tuning</b>);
                    K_OpenAI(<b>OpenAI<br>Fine-Tuning API</b>);
                    K_Anthropic(<b>Anthropic<br>Model Customization</b>);
                end
                
                J --> K_GCP;
                J --> K_OpenAI;
                J --> K_Anthropic;

                K_GCP -->|Updates Model| F_GCP;
                K_OpenAI -->|Updates Model| F_OpenAI;
                K_Anthropic -->|Updates Model| F_Anthropic;
            end
            
            subgraph "Analytics Pipeline"
                D_Results -->|Triggers on New Result| M(<b>Cloud Function</b><br>Streams Data to BigQuery);
                M -->|Loads Data| N(<b>Google BigQuery</b><br>Data Warehouse<br><i>Includes LLM provider/model metadata</i>);
                O(<b>Looker Studio</b><br>Performance Dashboard<br><i>Compares LLM performance</i>) -->|Queries Data| N;
                style N fill:#4A90E2,color:#fff;
                style O fill:#7E57C2,color:#fff;
            end
        end
    end
```
