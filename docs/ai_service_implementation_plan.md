# AI Service Implementation Plan

**Last Updated:** October 13, 2025
**Phase 1 Status:** ✅ Complete
**Related Documents:** [AI Service Design](./ai_service_design.md)

## Overview

This document breaks down the implementation of the AI Service into discrete, testable steps. Each phase builds upon previous work, progressively adding functionality while maintaining stability.

**Implementation Philosophy**:
- Start simple (one provider, one language)
- Integrate early (validate architecture before perfecting details)
- Add complexity incrementally (one dimension at a time)
- Harden for production after core functionality works

---

## Phase 1: Foundation & Single Provider PoC (OpenAI) ✅ COMPLETE

**Goal**: Get one LLM generating responses end-to-end in a controlled environment

**Completion Date**: October 13, 2025

### Step 1.1: Environment & Dependencies Setup ✅

**Status**: Complete

**Implemented**:
- LangChain packages installed (`langchain`, `langchain-openai`, `langchain-core`)
- OpenAI API configured via `.env`
- Project successfully imports langchain modules

**Files Modified**: `pyproject.toml`, `.env`

---

### Step 1.2: Basic Configuration Module ✅

**Status**: Complete

**Implemented**:
- `MODEL_PARAMS` dictionary with centralized configuration
- API key loading from environment
- Model-specific parameters (temperature, max_tokens)
- Fallback responses for error handling

**Files Modified**: `ai_service.py` (lines 31-62)

---

### Step 1.3: Single Provider Factory (OpenAI) ✅

**Status**: Complete

**Implemented**:
- `_create_openai_llm()` factory function (lines 220-252)
- ChatOpenAI instantiation with GPT-5
- Parameter passing (temperature from MODEL_PARAMS)
- API key validation
- **Important**: max_tokens removed due to GPT-5 compatibility issue

**Validation**: ✅ Factory creates working GPT-5 instances, generates quality responses

**Files Modified**: `ai_service.py`

---

### Step 1.4: Prompt Engineering - Basic Template ✅

**Status**: Complete

**Implemented**:
- English system prompt (lines 70-84)
- English user prompt (lines 87-89)
- `_create_prompt_template()` function (lines 132-160)
- ChatPromptTemplate with message structure
- Variable support: nickname, round_number, conversation_history, question

**Validation**: ✅ Prompts render correctly, AI responses natural and contextually appropriate

**Files Modified**: `ai_service.py` (prompt templates)

---

### Step 1.5: Conversation History Formatting ✅

**Status**: Complete

**Implemented**:
- `_format_conversation_history()` function (lines 96-129)
- Formats list of previous rounds into readable context
- Handles empty history (round 1)
- Consistent format with round numbers and Q&A pairs
- Implemented in `game_service.py` as `_extract_ai_conversation_history()` (lines 175-230)

**Validation**: ✅ History extraction tested, handles missing rounds gracefully

**Files Modified**: `ai_service.py` (helper functions), `game_service.py` (extraction logic)

---

### Step 1.6: Basic Chain Construction ✅

**Status**: Complete

**Implemented**:
- `_build_chain()` function (lines 167-213)
- LCEL pipe operator composition: `prompt | llm | output_parser`
- StrOutputParser for clean string output
- Returns Runnable chain

**Validation**: ✅ Chain executes successfully, returns string responses

**Files Modified**: `ai_service.py` (chain building functions)

---

### Step 1.7: Public Interface Function ✅

**Status**: Complete

**Implemented**:
- `generate_ai_response()` function (lines 282-381)
- Clean API with all necessary parameters
- Orchestrates full generation flow
- Error handling with fallback responses
- Logging integration

**Validation**: ✅ Function produces natural, contextually-aware AI responses

**Files Modified**: `ai_service.py` (public interface)

---

### Step 1.8: Basic Logging Integration ✅

**Status**: Complete

**Implemented**:
- Python logging at key points (lines 353-378)
- Includes game context (game_id, round_number, model_id)
- INFO level for successful generation
- ERROR/WARNING for failures and fallbacks

**Validation**: ✅ Logs provide clear debugging information

**Files Modified**: `ai_service.py`

---

### Step 1.9: LangSmith Integration ⏭️

**Status**: Skipped for Phase 1 (can add in Phase 4)

**Rationale**: Focus on core functionality first, LangSmith is optional for MVP

---

### Step 1.10: Integration Test with Game Service ✅

**Status**: Complete

**Implemented**:
- Renamed `_enqueue_ai_placeholder_answers()` to `_enqueue_ai_answers()`
- Integrated `ai_service.generate_ai_response()` call
- Updated all 4 call sites in game_service.py
- Added proper error handling with fallback
- Game data extraction for context

**Validation**: ✅ End-to-end integration successful, AI responses appear in game

**Files Modified**: `game_service.py` (lines 153-173, integration point)

---

### Phase 1 Summary

**Implementation Complete**: All core components working end-to-end

**Test Results**:
- ✅ GPT-5 model verified and accessible
- ✅ AI generates natural responses (2-5 sentences)
- ✅ Conversation history maintained across rounds
- ✅ Error handling with fallback responses tested
- ✅ Integration with game flow successful

**Test Files Created**:
- `test_factory.py` - Factory pattern validation
- `test_prompts.py` - Prompt rendering tests
- `test_history_extraction.py` - History extraction with mocks
- `test_chain.py` - Chain composition verification
- `test_ai_integration.py` - End-to-end real API tests
- `test_model_availability.py` - GPT-5 availability check
- `test_gpt5_params.py` - Parameter compatibility testing

**Known Issues Resolved**:
- GPT-5 max_tokens compatibility (removed parameter, uses prompt instructions)
- Empty response issue (fixed by removing max_tokens)

---

## Phase 2: Multi-Provider Support

**Goal**: Support all models from catalog, not just OpenAI

### Step 2.1: Provider Abstraction Layer

**What**: Create factory mapping and registry for all providers

**Achieves**:
- Maps model_catalog provider field to factory functions
- Central place to register new providers
- `_get_llm_instance()` can handle any model_id
- Clean separation between provider logic

**Validation**: Given any model_id from catalog, returns appropriate LLM instance

**Files Modified**: `ai_service.py` (provider registry)

---

### Step 2.2: Add Anthropic Provider

**What**: Implement factory for ChatAnthropic

**Achieves**:
- Claude models usable in games
- Demonstrates provider pattern works
- Different API key handling
- Anthropic-specific parameters handled

**Validation**: Can generate response using claude-opus-4.1 model

**Files Modified**: `ai_service.py`, `.env` (Anthropic key), `pyproject.toml` (langchain-anthropic)

---

### Step 2.3: Add Google Vertex AI Provider

**What**: Implement factory for ChatVertexAI

**Achieves**:
- Gemini models usable in games
- Handles different auth (service account, not API key)
- Google-specific parameter mapping
- Tests GCP integration

**Validation**: Can generate response using gemini-2.5-pro model

**Files Modified**: `ai_service.py`, `.env` (GCP credentials), `pyproject.toml` (langchain-google-vertexai)

---

### Step 2.4: Add xAI Provider (if available)

**What**: Implement factory for Grok, or document unavailability

**Achieves**:
- Complete model catalog coverage, or
- Documented limitation with workaround plan
- Future-proofing for when xAI LangChain support arrives

**Validation**: Either works with grok-4, or graceful error with clear message

**Files Modified**: `ai_service.py`, `.env` (xAI key if available)

---

### Step 2.5: Provider Switching Test

**What**: Test that game can use different models in different games

**Achieves**:
- Verify no cross-contamination between providers
- Each provider maintains its own state correctly
- Temperature/parameter differences work as expected
- API keys isolated properly

**Validation**: Create multiple games with different models, all generate successfully

**Testing**: Manual testing with multiple concurrent games

---

## Phase 3: Prompt Refinement & Language Support

**Goal**: Make responses believable and support Korean

### Step 3.1: Response Quality Evaluation

**What**: Play actual games and evaluate AI responses for believability

**Achieves**:
- Identify weaknesses in current prompts
- Test if responses are too robotic or too verbose
- Check if AI maintains consistency across rounds
- Gather data for prompt tuning

**Validation**: Document observations, identify specific failure patterns

**Deliverable**: Quality evaluation notes or document

---

### Step 3.2: System Prompt Iteration

**What**: Refine English system prompt based on evaluation

**Achieves**:
- Improved naturalness in responses
- Better adherence to length guidelines (2-5 sentences)
- More conversational tone
- Reduced "AI tells" (patterns that reveal AI)

**Validation**: New prompt produces noticeably more human-like responses

**Files Modified**: `ai_service.py` (English system prompt)

---

### Step 3.3: Korean Prompt Implementation

**What**: Create Korean version of system prompt with equivalent intent

**Achieves**:
- Support for Korean language games
- Culturally appropriate tone for Korean
- Same strategic goals as English prompt
- Bilingual AI service

**Validation**: Korean game produces appropriate Korean responses

**Files Modified**: `ai_service.py` (Korean system prompt)

---

### Step 3.4: Language-Aware Prompt Selection

**What**: Update prompt building logic to select correct language template

**Achieves**:
- Automatic selection based on game language setting
- No manual intervention needed
- Consistent prompt structure across languages
- Easy to add more languages later

**Validation**: English game uses English prompt, Korean game uses Korean prompt

**Files Modified**: `ai_service.py` (prompt selection logic)

---

### Step 3.5: Temperature Tuning

**What**: Adjust per-model temperature based on observed behavior

**Achieves**:
- Each model has optimal creativity level
- Natural style variation between models
- Reduces overly generic responses
- Maintains consistency within single model

**Validation**: Responses show appropriate variation without being incoherent

**Files Modified**: `ai_service.py` or configuration (model parameters)

---

## Phase 4: Production Hardening

**Goal**: Make service reliable for production deployment

### Step 4.1: Comprehensive Error Handling

**What**: Add try-catch blocks and error recovery at each integration point

**Achieves**:
- API failures don't crash game
- Network timeouts handled gracefully
- Invalid configurations caught early
- Clear error messages for debugging

**Validation**: Simulate API failure, service returns fallback without crashing

**Files Modified**: `ai_service.py` (error handling)

---

### Step 4.2: Retry Logic Implementation

**What**: Add LangChain retry wrapper or custom retry logic

**Achieves**:
- Transient errors automatically retried
- Exponential backoff prevents API hammering
- Max retry limit prevents infinite loops
- Logs retry attempts for monitoring

**Validation**: Simulate intermittent failure, see retries in logs, eventual success

**Files Modified**: `ai_service.py` (retry logic)

---

### Step 4.3: Fallback Response System

**What**: Implement language-appropriate fallback when all retries fail

**Achieves**:
- Game never completely fails due to AI issues
- Fallback is generic but grammatically correct
- Player experience degraded but not broken
- Logged for investigation

**Validation**: Force complete failure, fallback response used, game continues

**Files Modified**: `ai_service.py` (fallback responses)

---

### Step 4.4: Rate Limit Handling

**What**: Add detection and handling for API rate limit errors

**Achieves**:
- Recognizes rate limit specific errors
- Appropriate wait before retry
- Logs rate limit hits for capacity planning
- Doesn't waste retries on rate limits

**Validation**: Trigger rate limit, see appropriate handling and logging

**Files Modified**: `ai_service.py` (rate limit detection)

---

### Step 4.5: Production Logging Configuration

**What**: Set up environment-based log levels and structured logging

**Achieves**:
- Development: verbose logs for debugging
- Production: INFO level with JSON format
- Easy to change without code changes
- Ready for log aggregation tools

**Validation**: Different log output in dev vs prod configuration

**Files Modified**: `logging_config.py`, `config.py` (environment settings)

---

### Step 4.6: LangSmith Sampling Implementation

**What**: Add environment flag and sampling logic for production traces

**Achieves**:
- Can disable LangSmith entirely if needed
- Can sample (e.g., 10% of games traced)
- Reduces production costs
- Maintains development full tracing

**Validation**: With sampling at 0.1, only ~10% of generations traced

**Files Modified**: `ai_service.py`, `config.py` (sampling logic)

---

### Step 4.7: Performance Monitoring Hooks

**What**: Add timing metrics and performance logging

**Achieves**:
- Track generation latency per model
- Identify slow providers
- Token usage tracking (via LangSmith)
- Foundation for alerting

**Validation**: Logs include duration for each generation call

**Files Modified**: `ai_service.py` (timing instrumentation)

---

### Step 4.8: Configuration Validation

**What**: Startup checks that all required config is present

**Achieves**:
- Fast failure on misconfiguration
- Clear error messages about missing keys
- Prevents silent failures in production
- Confidence in deployment

**Validation**: Missing API key causes immediate, clear error on startup

**Files Modified**: `ai_service.py` or `config.py` (validation logic)

---

## Phase 5: Testing & Validation

**Goal**: Ensure reliability before production

### Step 5.1: Unit Tests - Prompt Formatting

**What**: Test prompt building logic with various inputs

**Achieves**:
- Conversation history formats correctly
- Empty history handled
- All variables substituted properly
- Edge cases covered

**Validation**: Test suite passes, covers edge cases

**Files Created**: `tests/test_ai_service.py` (prompt tests)

---

### Step 5.2: Unit Tests - Provider Factories

**What**: Test each provider factory returns correct LLM instance

**Achieves**:
- Each factory creates correct class type
- Parameters passed correctly
- API keys loaded properly
- Mock-able for testing

**Validation**: Test suite passes, mocks work correctly

**Files Modified**: `tests/test_ai_service.py` (provider tests)

---

### Step 5.3: Integration Tests - Mock LLM

**What**: Test full generation flow with mocked LLM responses

**Achieves**:
- Full flow tested without API costs
- Deterministic test behavior
- Fast test execution
- Validates integration logic

**Validation**: Tests run quickly, reliably pass

**Files Modified**: `tests/test_ai_service.py` (integration tests)

---

### Step 5.4: Integration Tests - Real API (Optional)

**What**: Test with real API calls in CI/CD (optional, careful with costs)

**Achieves**:
- Validates real API integration
- Catches API changes
- Tests actual provider behavior
- Confidence in production readiness

**Validation**: Real API tests pass occasionally (not every commit)

**Files Modified**: `tests/test_ai_service_integration.py` (real API tests)

---

### Step 5.5: Manual End-to-End Game Testing

**What**: Play complete 3-round games with AI players

**Achieves**:
- Validates entire game loop works
- Tests AI response quality in context
- Identifies usability issues
- Tests consistency across rounds

**Validation**: Can complete full games, AI responses believable

**Testing**: Manual gameplay sessions

---

### Step 5.6: Multi-Game Stress Test

**What**: Run multiple games concurrently to test stability

**Achieves**:
- Identifies concurrency issues
- Tests API rate limits in practice
- Validates error handling under load
- Confidence in reliability

**Validation**: Multiple concurrent games complete successfully

**Testing**: Concurrent game simulation

---

## Summary of Key Components

### Foundation (Phase 1)
- Configuration loading
- Single provider factory
- Prompt templates
- Chain construction
- Public interface
- Logging basics

### Scalability (Phase 2)
- Provider abstraction
- Multiple LLM providers
- Catalog integration

### Quality (Phase 3)
- Prompt refinement
- Multi-language support
- Response tuning

### Reliability (Phase 4)
- Error handling
- Retry logic
- Fallbacks
- Production config
- Monitoring

### Confidence (Phase 5)
- Unit tests
- Integration tests
- Manual validation
- Stress testing

---

## Critical Success Factors

**After Phase 1**:
- Can generate AI responses using OpenAI
- Responses appear in game when answers are revealed
- Basic logging works

**After Phase 2**:
- All catalog models work
- Can switch between providers seamlessly

**After Phase 3**:
- AI responses are believably human-like
- Both English and Korean work correctly
- Different models have distinct styles

**After Phase 4**:
- Service doesn't crash on errors
- Production-ready logging and monitoring
- Cost controls in place

**After Phase 5**:
- Test coverage adequate
- Confidence in reliability
- Ready for deployment

---

## Implementation Notes

### Sequential Dependencies
- Phase 2 requires Phase 1 completion (can't abstract multiple providers without one working)
- Phase 3 can partially overlap with Phase 2 (prompt tuning doesn't require all providers)
- Phase 4 can start after Phase 1 (error handling independent of provider count)
- Phase 5 should be ongoing (write tests as you implement features)

### Estimated Effort
- **Phase 1**: 1-2 days (core functionality)
- **Phase 2**: 1 day (pattern already established)
- **Phase 3**: 1-2 days (iterative prompt tuning)
- **Phase 4**: 1 day (systematic hardening)
- **Phase 5**: Ongoing (write tests alongside implementation)

**Total**: ~5-7 days for complete, production-ready implementation

### Risk Mitigation
- **Risk**: xAI provider unavailable
  - **Mitigation**: Document limitation, keep model in catalog for future

- **Risk**: Prompts produce poor quality responses
  - **Mitigation**: Phase 3 dedicated to iteration, can adjust without changing architecture

- **Risk**: API costs higher than expected
  - **Mitigation**: Phase 4 includes sampling and monitoring to control costs

---

**Document Status**: Implementation plan ready. Begin with Phase 1, Step 1.1.
