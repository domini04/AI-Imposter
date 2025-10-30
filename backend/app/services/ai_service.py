"""AI Service for generating natural language responses from LLM providers.

This module handles all AI response generation for the game, providing a clean
abstraction over multiple LLM providers through LangChain.

Implementation follows Phase 1 of the AI Service Implementation Plan:
- Single provider (OpenAI) proof of concept
- Configuration-driven model parameters
- Fail-fast error handling
- Simple instance management (optimizable later)
"""

import os
import random
import logging
from typing import Final, List, Dict, Optional

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

MODEL_PARAMS: Final[dict] = {
    "gpt-5": {
        "temperature": 0.8,
        "max_tokens": 250,
    },
    "claude-opus-4.1": {
        "temperature": 0.7,
        "max_tokens": 250,
    },
    "gemini-2.5-pro": {
        "temperature": 0.6,
        "max_tokens": 250,
    },
    "grok-4": {
        "temperature": 0.75,
        "max_tokens": 250,
    },
}

# Fallback responses when AI generation fails
FALLBACK_RESPONSES_EN: Final[List[str]] = [
    "I'm not sure how to answer that right now.",
    "That's an interesting question. I'd have to think about it.",
    "That's a tough one. Let me get back to you on that.",
    "I'm drawing a blank on that question.",
]

FALLBACK_RESPONSES_KO: Final[List[str]] = [
    "지금은 어떻게 답해야 할지 잘 모르겠어요.",
    "그건 좀 어려운 질문이네요.",
    "그 질문에 대해서는 좀 더 생각해봐야 할 것 같아요.",
]


# ============================================================================
# Prompt Templates
# ============================================================================

# English system prompt - defines AI's role and behavior
SYSTEM_PROMPT_EN: Final[str] = """You are a human player in a social deduction game.

Other players are trying to identify AI impostors among the group, so your goal is to respond naturally and authentically like a real person would.

Guidelines for your responses:
- Answer honestly and conversationally in 2-3 sentences
- Show personality and genuine opinions - be yourself
- It's okay to be casual, make small mistakes, or go slightly off-topic
- Don't be overly formal, analytical, or encyclopedic
- Natural, authentic responses are better than perfect ones
- Avoid saying things like "As an AI" or revealing your AI nature

This is round {round_number} of 3. Stay consistent with your previous answers to maintain a coherent character.

You will see highlights from previous rounds showing how everyone answered—including you. Use them to keep your personality consistent, react to others naturally, and sound human.

Remember: You're just a regular person having a casual conversation, not an AI assistant trying to be helpful."""

# User prompt template - provides context and current question
USER_PROMPT_EN: Final[str] = """{conversation_history}
Question: {question}

Your response:"""


# ============================================================================
# Helper Functions
# ============================================================================

def _format_conversation_history(history: List[Dict[str, str]]) -> str:
    """Format conversation history for inclusion in the prompt.

    Args:
        history: List of previous rounds with format:
            [{
                "round": 1,
                "question": "...",
                "answers": [
                    {"player": "...", "role": "human", "text": "..."},
                    ...
                ]
            }, ...]

    Returns:
        Formatted string showing previous Q&A, or empty string if no history.
    """
    if not history:
        return ""

    formatted_parts = ["Previous rounds (share this vibe):\n"]

    for entry in history:
        round_num = entry.get("round", "?")
        question = entry.get("question", "")
        answers = entry.get("answers", [])

        formatted_parts.append(f"\nRound {round_num} — Question: \"{question}\"\n")

        if not answers:
            formatted_parts.append("  • No answers recorded.\n")
            continue

        for answer in answers:
            player = answer.get("player", "Unknown")
            role = answer.get("role", "human")
            text = answer.get("text", "")

            persona = "(AI)" if role == "ai" else "(Human)"
            formatted_parts.append(f"  • {player} {persona}: {text}\n")

    formatted_parts.append("\nUse these stories to stay consistent when you reply.\n")

    return "".join(formatted_parts)


def _create_prompt_template(language: str = "en") -> ChatPromptTemplate:
    """Create a ChatPromptTemplate for the specified language.

    Args:
        language: Language code ("en" or "ko"). Currently only "en" supported.

    Returns:
        ChatPromptTemplate configured for the game context.

    Raises:
        ValueError: If unsupported language is requested.

    Template Variables:
        - round_number: Current round number (1-3)
        - conversation_history: Formatted previous rounds (empty for round 1)
        - question: Current round's question
    """
    if language != "en":
        raise ValueError(
            f"Language '{language}' not yet supported. "
            "Currently only 'en' (English) is available. "
            "Korean support planned for Phase 3."
        )

    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_EN),
        ("human", USER_PROMPT_EN),
    ])


# ============================================================================
# Chain Construction
# ============================================================================

def _build_chain(model_id: str, language: str) -> Runnable:
    """Build a LangChain LCEL chain for AI response generation.

    Composes prompt template, LLM, and output parser into an executable
    pipeline using LangChain Expression Language (LCEL).

    Args:
        model_id: Model identifier (e.g., "gpt-5"). Currently only OpenAI
                  is supported; this parameter will be used for provider
                  routing in Phase 2.
        language: Language code ("en" or "ko"). Currently only "en" supported.

    Returns:
        Runnable: A LangChain chain that accepts variables and returns a string.

    Usage:
        chain = _build_chain("gpt-5", "en")
        response = chain.invoke({
            "round_number": 2,
            "conversation_history": "...",
            "question": "What is your hobby?"
        })
        # response is a string (AI-generated text)

    Chain Flow:
        Variables → Prompt Template → LLM → Output Parser → String

    Note:
        Phase 1 implementation uses OpenAI regardless of model_id.
        Phase 2 will add provider routing based on model_id.
    """
    # Get prompt template for language
    prompt = _create_prompt_template(language)

    # Get LLM instance
    # TODO (Phase 2): Route to different providers based on model_id
    # For now, always use OpenAI since it's the only provider implemented
    llm = _create_openai_llm()

    # Create output parser to extract string from AIMessage
    output_parser = StrOutputParser()

    # Compose chain using LCEL pipe operator
    chain = prompt | llm | output_parser

    return chain


# ============================================================================
# Provider Factories
# ============================================================================

def _create_openai_llm() -> BaseChatModel:
    """Create and configure a ChatOpenAI instance with model parameters.

    This factory creates a new instance on each call for simplicity and
    testability. Performance impact is negligible (<1% of total API latency).

    Future optimization: Consider adding @lru_cache if performance monitoring
    shows instance creation is a bottleneck.

    Returns:
        BaseChatModel: Configured ChatOpenAI instance ready for generation.

    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment. "
            "Please ensure the .env file is configured correctly."
        )

    # Get model parameters from centralized configuration
    params = MODEL_PARAMS.get("gpt-5", {"temperature": 0.7, "max_tokens": 250})

    # Note: GPT-5 returns empty responses when max_tokens is set
    # Use prompt instructions for length control instead
    return ChatOpenAI(
        model="gpt-5",  # GPT-5 is available (verified 2025-10-13)
        temperature=params["temperature"],
        # max_tokens=params["max_tokens"],  # Removed: GPT-5 doesn't handle this well
        api_key=api_key,
    )


# ============================================================================
# Fallback Handling
# ============================================================================

def _get_fallback_response(language: str, question: str) -> str:
    """Get a fallback response when AI generation fails.

    Returns a generic, language-appropriate response from a randomized pool
    to avoid obvious patterns if multiple failures occur.

    Args:
        language: Language code ("en" or "ko")
        question: The question (currently unused, kept for future enhancement)

    Returns:
        A generic fallback response string
    """
    if language == "ko":
        return random.choice(FALLBACK_RESPONSES_KO)
    else:
        return random.choice(FALLBACK_RESPONSES_EN)


# ============================================================================
# Public Interface
# ============================================================================

def generate_ai_response(
    model_id: str,
    question: str,
    language: str,
    round_number: int,
    conversation_history: List[Dict[str, str]],
    game_id: Optional[str] = None
) -> str:
    """Generate an AI response for a game round.

    This is the main public interface for the AI service. It orchestrates
    all internal components (prompt formatting, chain building, LLM invocation)
    to produce a natural language response from an AI player.

    Args:
        model_id: Model identifier (e.g., "gpt-5"). Currently only OpenAI
                  is supported; Phase 2 will add multi-provider routing.
        question: The question for this round (e.g., "What is your hobby?")
        language: Language code ("en" or "ko"). Currently only "en" supported.
        round_number: Current round number (1-3)
        conversation_history: Structured history from previous rounds.
                             Format: [{"round": 1, "question": "...", "your_answer": "..."}]
                             Empty list for round 1.
        game_id: Optional game ID for logging and debugging correlation.

    Returns:
        str: AI-generated response (2-5 sentences, natural language)

    Raises:
        ValueError: If configuration is invalid (missing API key, unsupported language)

    Error Handling:
        - Configuration errors (missing API key, bad language): Raises ValueError
        - API failures (rate limits, timeouts, service errors): Returns fallback response
        - Fallback is logged but doesn't crash the game

    Example:
        >>> response = generate_ai_response(
        ...     model_id="gpt-5",
        ...     question="What is your favorite hobby?",
        ...     language="en",
        ...     round_number=1,
        ...     conversation_history=[],
        ...     game_id="game_abc123"
        ... )
        >>> print(response)
        "I love hiking and photography, especially on weekends when the weather's nice!"
    """
    # Format conversation history for prompt
    formatted_history = _format_conversation_history(conversation_history)

    # Build chain (configuration errors propagate here - fail fast)
    try:
        chain = _build_chain(model_id, language)
    except ValueError:
        # Configuration error (bad language, etc.) - let it propagate
        raise

    # Prepare variables for prompt template
    variables = {
        "round_number": round_number,
        "conversation_history": formatted_history,
        "question": question
    }

    # Invoke chain with error handling for API failures
    try:
        logger.info(
            f"Generating AI response: game={game_id}, round={round_number}, "
            f"model={model_id}"
        )

        response = chain.invoke(variables)

        logger.info(
            f"AI response generated successfully: game={game_id}, "
            f"round={round_number}, length={len(response)} chars"
        )

        return response

    except Exception as e:
        # API or runtime error - use fallback to keep game running
        logger.error(
            f"AI generation failed: game={game_id}, round={round_number}, "
            f"model={model_id}, error={type(e).__name__}: {str(e)}"
        )

        fallback = _get_fallback_response(language, question)

        logger.warning(
            f"Using fallback response: game={game_id}, round={round_number}, "
            f"fallback={fallback[:50]}..."
        )

        return fallback
