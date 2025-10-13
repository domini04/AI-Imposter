# AI Service Design

**Last Updated:** October 13, 2025
**Status:** Phase 1 Complete, Multi-Provider Support Pending

## 1. Overview

The AI Service generates natural language responses for AI players to participate convincingly in the social deduction game. It integrates multiple LLM providers through LangChain to enable comparative performance analysis and future fine-tuning.

### Core Objective
Generate contextually appropriate, human-like responses to round questions that blend in with human players, making the game challenging and meaningful.

---

## 2. Requirements

### 2.1 Functional Requirements

- **Input**: Game context (question, language, round number, conversation history, model selection)
- **Output**: Natural language response (2-5 sentences, free-form text)
- **Timing**: Synchronous generation at round start (response time not critical due to simultaneous reveal)

### 2.2 Integration Points

- **Consumer**: `game_service._enqueue_ai_placeholder_answers()`
- **Called from**: `start_game()`, `tally_answers()`, `tally_votes()`
- **Storage**: Responses written to Firestore `pending_messages` subcollection

### 2.3 Multi-Provider Support

Must support all models from `model_catalog.py`:
- OpenAI (GPT-5)
- Anthropic (Claude Opus 4.1)
- Google Vertex AI (Gemini 2.5 Pro)
- xAI (Grok 4)

### 2.4 Response Quality Goals

- **Naturalness**: Conversational, human-like tone
- **Relevance**: Directly addresses the question
- **Consistency**: Maintains coherence with previous round answers
- **Variation**: Avoids detectable patterns across responses
- **Language**: Supports English and Korean

---

## 3. Architecture

### 3.1 Service Structure

```
ai_service.py
├── Public Interface
│   └── generate_ai_response() → str
│
├── LangChain Integration
│   ├── _get_llm_instance() → BaseChatModel
│   ├── _build_prompt_chain() → Runnable
│   └── _invoke_with_retry() → str
│
├── Provider Factories
│   ├── _create_openai_llm()
│   ├── _create_anthropic_llm()
│   ├── _create_google_llm()
│   └── _create_xai_llm()
│
├── Prompt Engineering
│   ├── _build_system_prompt()
│   ├── _format_conversation_history()
│   └── _create_prompt_template()
│
└── Configuration
    └── _load_config() → AIConfig
```

### 3.2 Key Data Structures

**AIContext**: Game context needed for generation (model_id, question, language, round_number, player_nickname, conversation_history)

**ConversationTurn**: One round of Q&A (round, question, your_answer)

**AIConfig**: Service configuration (api_keys, model_params, system_prompts, timeout, retry_attempts)

**ModelParams**: Per-model settings (temperature, max_tokens)

---

## 4. Prompt Engineering Strategy

### 4.1 Design Philosophy

**Single Flexible Prompt Per Language**: Use one well-crafted prompt that allows natural personality variation without forcing rigid personas.

**Rationale for Not Using Multiple Personas**:
- Confounds performance metrics (model capability vs. persona effectiveness)
- Complicates training pipeline (unclear learning signal)
- Creates game balance issues (players pattern-match personas)

**Natural Variation Through**:
- Temperature differences per model (0.6-0.8 range)
- Conversation history (personality emerges organically over rounds)
- Each model's inherent characteristics

### 4.2 Prompt Characteristics

**System Prompt Goals**:
- Instruct AI to pretend to be human in social deduction game
- Encourage conversational, casual tone with personality
- Allow slight off-topic remarks if natural
- Emphasize brevity (2-5 sentences)
- Warn against being too perfect or robotic
- Include context: player nickname, current round number

**User Prompt Structure**:
- Formatted conversation history from previous rounds
- Current round question
- Response invitation

**Language Support**: Separate prompts for English and Korean with equivalent intent

### 4.3 Temperature Strategy

Different temperature per model creates natural style diversity:
- GPT-5: 0.8 (more creative)
- Claude Opus 4.1: 0.7 (balanced)
- Gemini 2.5 Pro: 0.6 (more focused)
- Grok 4: 0.75 (experimental)

This is a model parameter, not a persona, so metrics remain clean.

---

## 5. LangChain Integration

### 5.1 Chain Architecture

Use **LangChain Expression Language (LCEL)** for composable chains:
- Build prompt from system + user templates
- Pipe through LLM instance
- Parse output as string
- No structured output parsing (raw text sufficient)

### 5.2 Provider Abstraction

**Factory Pattern**: Map model catalog's `provider` field to LangChain provider classes
- Each factory initializes provider-specific chat model
- Abstracts API key management and parameters
- Returns standardized `BaseChatModel` interface

### 5.3 Error Handling

**Retry Strategy**: Use LangChain's built-in retry with exponential backoff
- Retry on API errors, timeouts
- Max 3 attempts
- Log failures with structured logging

**Fallback Strategy**: Return generic response if all retries fail
- Language-appropriate fallback message
- Log error for debugging
- Game continues without blocking

---

## 6. Observability & Logging

### 6.1 Two-Tier Logging Strategy

**LangSmith (LLM-Specific Observability)**:
- Purpose: Trace LLM chain execution, prompt debugging, token usage tracking
- Scope: Prompt construction, LLM API calls, response parsing, token counts
- Configuration: Environment variables (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`)
- Usage: Enabled in development (100% tracing), optional/sampled in production

**Backend Logging (Application Flow)**:
- Purpose: Application-level debugging, integration errors, business logic
- Scope: Game state transitions, Firestore operations, authentication, non-LLM errors
- Implementation: Python `logging` module with structured output
- Levels: INFO (always), DEBUG (development), WARNING/ERROR (issues)

### 6.2 Correlation Strategy

**Include correlation IDs in both systems**:
- Add `game_id` parameter to AI service functions
- Include game context (`game_id`, `round_number`, `model_id`) in backend logs
- Add same context as metadata to LangSmith traces
- Enables cross-system debugging: search both systems by `game_id`

**Log Context Structure**:
- Backend: `{"game_id": "abc123", "model_id": "gpt-5", "round_number": 2}`
- LangSmith: Run name `game_abc123_round_2`, tags `[model:gpt-5, lang:en]`, metadata `{game_id: abc123}`

### 6.3 Production Considerations

**LangSmith in Production**:
- Cost: Free tier limited to 5K traces/month
- Strategy: Toggle via environment flag, sample traces (e.g., 10-20%)
- Configuration: `ENABLE_LANGSMITH`, `LANGSMITH_SAMPLE_RATE` settings

**Structured Logging**:
- Development: Human-readable text format
- Production: JSON format for log aggregation (Cloud Logging, Datadog)
- Includes timestamp, level, logger name, message, context fields

---

## 7. Configuration Management

### 7.1 Environment Variables

**Required API Keys** (from environment):
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_APPLICATION_CREDENTIALS` (path to service account JSON)
- `XAI_API_KEY` (if supported)

**LangSmith Configuration** (optional):
- `LANGCHAIN_TRACING_V2=true` (enable tracing)
- `LANGCHAIN_API_KEY` (LangSmith API key)
- `LANGCHAIN_PROJECT` (project name for organizing traces)

### 7.2 Model Parameters

Per-model configuration stored in code or config file:
- Temperature (0.6-0.8 range, varies per model)
- Max tokens (150 target for 2-5 sentences)
- Timeout (30 seconds default)
- Retry attempts (3 default)

---

## 7. Integration with Game Service

### 7.1 Changes Required

**Function Signature Update**: `_enqueue_ai_placeholder_answers()` needs `game_data` parameter to extract:
- Current question
- Game language
- Selected AI model ID
- Previous rounds for history

**Callers to Update**:
- `start_game()`
- `tally_answers()`
- `tally_votes()`

**New Helper Function**: `_build_conversation_history()` to extract AI's previous answers from Firestore messages collection

### 7.2 Error Handling in Game Service

AI generation failures should not crash the game:
- Try-catch around `generate_ai_response()` call
- Use fallback message on error
- Log error for debugging
- Game continues

---

## 8. Testing Strategy

### 8.1 Unit Tests
- Prompt template formatting with various inputs
- Provider factory returns correct LangChain class
- Conversation history formatting
- Configuration loading

### 8.2 Integration Tests
- Mock LLM responses to test full flow
- Error handling and fallback behavior
- Retry logic

### 8.3 Manual In-Game Testing
- AI responds appropriately to English/Korean questions
- Consistency across 3 rounds
- Natural conversational tone
- Distinct styles between models
- No errors under normal conditions

---

## 9. Dependencies

**Add to `pyproject.toml`**:
- `langchain` (>=0.3.0)
- `langchain-openai` (>=0.2.0)
- `langchain-anthropic` (>=0.2.0)
- `langchain-google-vertexai` (>=2.0.0)
- `langchain-core` (>=0.3.0)

**External Services Required**:
- OpenAI API account
- Anthropic API account
- Google Cloud Platform (Vertex AI enabled)
- xAI API account (if available)

---

## 10. Implementation Phases

### Phase 1: Single Provider PoC (OpenAI)
- Set up LangChain with OpenAI
- Implement basic prompt template
- Integrate with `game_service.py`
- Test in local game

### Phase 2: Multi-Provider Support
- Add remaining providers (Anthropic, Google, xAI)
- Test provider switching
- Verify distinct model styles

### Phase 3: Prompt Refinement
- Test believability in actual gameplay
- Tune system prompts
- Implement Korean language support
- Adjust temperatures per model

### Phase 4: Production Hardening
- Comprehensive error handling
- Structured logging
- Rate limit handling
- Performance monitoring

---

## 11. Success Criteria

The AI service is successful when:

1. ✅ AI players complete games without errors
2. ✅ Human players cannot easily identify AI (>40% survival rate target)
3. ✅ AI maintains coherent personality across 3 rounds
4. ✅ Different models show distinct conversational styles
5. ✅ < 1% failure rate in production
6. ✅ New models can be added easily
7. ✅ Logs provide clear debugging information

---

## 12. Implementation Decisions & Status

**Phase 1 Implementation Completed:** October 13, 2025
**Context:** Single-provider proof of concept with OpenAI GPT-5

### Decision 1: Model Name Mapping
- **Approach:** Hardcode model name in factory function
- **Implementation:** Use `"gpt-5"` directly in ChatOpenAI instantiation
- **Rationale:** Pragmatic YAGNI - test with actual API names, refactor if needed
- **Status:** ✅ Approved

### Decision 2: Temperature Storage
- **Approach:** Configuration Dictionary (Module-Level)
- **Implementation:**
  ```python
  MODEL_PARAMS = {
      "gpt-5": {"temperature": 0.8, "max_tokens": 150},
      "claude-opus-4.1": {"temperature": 0.7, "max_tokens": 150},
      "gemini-2.5-pro": {"temperature": 0.6, "max_tokens": 150},
      "grok-4": {"temperature": 0.75, "max_tokens": 150}
  }
  ```
- **Rationale:**
  - Centralized configuration for easy comparison and tuning
  - Supports Phase 3 prompt refinement workflow
  - Self-documenting configuration
  - Easy to extend with additional parameters
- **Status:** ✅ Approved

### Decision 3: Error Handling (Missing API Keys)
- **Approach:** Raise exception immediately on missing API key
- **Implementation:** `raise ValueError("OPENAI_API_KEY not found in environment")`
- **Rationale:** Fail-fast production mindset, clear error messages, prevents silent failures
- **Status:** ✅ Approved

### Decision 4: Instance Reuse Strategy
- **Approach:** Create new instance per call (Approach A)
- **Implementation:** Factory creates fresh ChatOpenAI instance each time
- **Rationale:**
  - Simplicity first - easier to debug and test
  - Performance impact negligible (<1% of total API latency)
  - Thread-safe by default (no shared state)
  - Easy to optimize later with `@lru_cache` if needed (Approach C)
- **Future Optimization:** Consider LRU caching if performance monitoring shows need
- **Status:** ✅ Implemented

### Decision 6: GPT-5 max_tokens Parameter Issue
- **Issue Discovered:** October 13, 2025
- **Problem:** GPT-5 returns empty strings when `max_tokens` parameter is specified
- **Solution:** Removed `max_tokens` parameter from factory, rely on prompt instructions for length control
- **Implementation:** Line 247-250 in `ai_service.py` - max_tokens commented out with explanation
- **Verification:** Tested with and without parameter - GPT-5 generates excellent responses without max_tokens
- **Status:** ✅ Resolved

### Environment Configuration
- **API Key Source:** `.env` file at project root
- **Loading Mechanism:** `python-dotenv` (already configured via `app/core/config.py`)
- **Variable Name:** `OPENAI_API_KEY`

### Decision 5: Human Answers in AI Prompt (Phase 1)
- **Approach:** AI does NOT see human answers for current round
- **Implementation:** Prompt includes only question + AI's own history
- **Rationale:**
  - Simpler to implement (no timing dependencies)
  - Establishes baseline AI quality without mimicry assistance
  - Cleaner separation of concerns
  - Easier to test and debug
- **Future Enhancement (Phase 3/4):** If AI is too easy to detect:
  - Add human answers to prompt before AI generation
  - Use "Wait for AI, Then Simultaneous Reveal" pattern (Solution B)
  - Implementation: Collect human answers → brief loading (1-3s) → AI generates → all revealed together
  - Maintains simultaneous reveal principle
  - Fallback to generic answer if AI generation fails
- **Status:** ✅ Approved (simple design now, enhancement path defined)

---

## 13. Open Questions

- **xAI Integration**: Is `langchain-xai` package available? May need custom implementation.
- **Rate Limits**: Do we need request queuing for production traffic?
- **Cost Analysis**: What are expected API costs per game?

## 14. Future Enhancements

- **Async Generation**: Parallelize multiple AI responses
- **Response Caching**: Cache responses to reduce API costs
- **Fine-Tuned Models**: Integrate custom models after training pipeline
- **Additional Languages**: Expand beyond English/Korean

---

## 15. Phase 1 Implementation Summary

**Completion Date:** October 13, 2025

### Components Implemented:
- ✅ Configuration management with MODEL_PARAMS dictionary
- ✅ OpenAI provider factory (`_create_openai_llm()`)
- ✅ English prompt templates (system + user)
- ✅ Conversation history formatting (`_format_conversation_history()`)
- ✅ Prompt template builder (`_create_prompt_template()`)
- ✅ LCEL chain construction (`_build_chain()`)
- ✅ Public interface (`generate_ai_response()`)
- ✅ Error handling with fallback responses
- ✅ Python logging integration
- ✅ Game service integration (`_enqueue_ai_answers()`)
- ✅ Conversation history extraction from Firestore (`_extract_ai_conversation_history()`)

### Validation Results:
- ✅ GPT-5 model verified and working
- ✅ AI generates natural, contextually-aware responses
- ✅ Conversation history maintained across rounds
- ✅ Error handling with graceful fallbacks tested
- ✅ End-to-end integration with game flow successful

### Known Limitations (Phase 1):
- Single provider only (OpenAI)
- English language only
- No LangSmith tracing (can add in Phase 4)
- Basic logging (no structured JSON)
- No retry logic (can add in Phase 4)

### Next Steps:
- Phase 2: Add Anthropic, Google, xAI providers
- Phase 3: Add Korean language support, tune prompts
- Phase 4: Production hardening (retry, structured logging, monitoring)

---

**Document Status**: Phase 1 complete and validated. Multi-provider support pending.
