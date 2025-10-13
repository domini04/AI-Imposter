"""Quick verification script for Step 1.3: OpenAI factory function.

Run this from the backend directory to verify the factory works:
    python test_factory.py
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables (mimics what config.py does in the app)
from app.core import config  # This automatically loads .env

from app.services.ai_service import _create_openai_llm, MODEL_PARAMS


def test_factory():
    """Test the OpenAI factory function."""
    print("=" * 70)
    print("Step 1.3 Verification: OpenAI Factory Function")
    print("=" * 70)

    # Test 1: Configuration loading
    print("\n✓ Test 1: Model parameters configuration")
    print(f"  MODEL_PARAMS loaded: {len(MODEL_PARAMS)} models")
    for model_id, params in MODEL_PARAMS.items():
        print(f"    - {model_id}: temp={params['temperature']}, max_tokens={params['max_tokens']}")

    # Test 2: Factory function
    print("\n✓ Test 2: Factory function instantiation")
    try:
        llm = _create_openai_llm()
        print(f"  Instance created: {type(llm).__name__}")
        print(f"  Model name: {llm.model_name}")
        print(f"  Temperature: {llm.temperature}")
        print(f"  Max tokens: {llm.max_tokens}")
    except ValueError as e:
        print(f"  ✗ Error: {e}")
        print("  Ensure OPENAI_API_KEY is set in .env file")
        return False

    # Test 3: Return type
    print("\n✓ Test 3: Return type validation")
    from langchain_core.language_models import BaseChatModel
    if isinstance(llm, BaseChatModel):
        print(f"  ✓ Returns BaseChatModel interface")
    else:
        print(f"  ✗ Does not return BaseChatModel")
        return False

    print("\n" + "=" * 70)
    print("✓ All checks passed! Factory function is working correctly.")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_factory()
    sys.exit(0 if success else 1)
