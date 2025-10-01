
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Ensure environment variables from the project root are loaded before evaluating the skip condition.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def has_gemini_api_key() -> bool:
    return bool(os.getenv("GOOGLE_API_KEY"))


@pytest.mark.integration
@pytest.mark.skipif(not has_gemini_api_key(), reason="GOOGLE_API_KEY not configured; skipping Gemini integration test.")
def test_gemini_integration_call():
    """Ensure we can invoke the configured Gemini model using LangChain."""

    model = ChatGoogleGenerativeAI(model="gemini-2.5-pro")

    response = model.invoke("Say hello.")
    assert response.content
    print(f"Gemini response: {response.content[:50]}...")
