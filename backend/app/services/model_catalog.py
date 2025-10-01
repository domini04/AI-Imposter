"""Central catalog of supported LLM configurations.

This module acts as the single source of truth for the AI models that can be
selected when creating a game. Each entry includes metadata that can be safely
exposed via the public API while keeping provider-specific configuration (like
API keys or fine-tuned versions) encapsulated elsewhere.
"""

from __future__ import annotations

from typing import Final, List, TypedDict


class ModelConfig(TypedDict):
    """Structure describing an available LLM configuration."""

    id: str
    provider: str
    display_name: str
    description: str


_MODEL_CATALOG: Final[List[ModelConfig]] = [
    {
        "id": "gemini-2.5-pro",
        "provider": "google",
        "display_name": "Gemini 2.5 Pro",
        "description": "Google DeepMind's flagship Gemini model with multimodal reasoning support.",
    },
    {
        "id": "gpt-5",
        "provider": "openai",
        "display_name": "GPT-5",
        "description": "OpenAI's latest GPT series release optimized for advanced problem solving and dialogue.",
    },
    {
        "id": "claude-opus-4.1",
        "provider": "anthropic",
        "display_name": "Claude Opus 4.1",
        "description": "Anthropic's top-tier Claude model tuned for deep, reliable analysis.",
    },
    {
        "id": "grok-4",
        "provider": "xai",
        "display_name": "Grok 4",
        "description": "xAI's Grok model focused on high-context reasoning and code generation.",
    },
]


def list_models() -> List[ModelConfig]:
    """Return all supported model configurations."""

    # Return a shallow copy to prevent accidental mutation by callers.
    return list(_MODEL_CATALOG)

