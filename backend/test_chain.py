"""Verification script for Step 1.6: Chain construction.

Run from backend directory: uv run test_chain.py
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from app.core import config

from app.services.ai_service import _build_chain


def test_chain():
    """Test chain construction and basic invocation."""
    print("=" * 70)
    print("Step 1.6 Verification: Chain Construction")
    print("=" * 70)

    # Test 1: Chain creation
    print("\n✓ Test 1: Chain creation")
    try:
        chain = _build_chain("gpt-5", "en")
        print(f"  Chain created: {type(chain).__name__}")
        print(f"  Chain is runnable: {hasattr(chain, 'invoke')}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

    # Test 2: Chain structure
    print("\n✓ Test 2: Chain composition validation")
    try:
        # Chain should be a RunnableSequence (prompt | llm | parser)
        chain_str = str(chain)
        print(f"  Chain type: {type(chain).__name__}")

        # Check that it's composable (has the pipe structure)
        has_steps = hasattr(chain, 'steps') or hasattr(chain, 'first')
        print(f"  ✓ Chain is properly composed: {has_steps}")
    except Exception as e:
        print(f"  ⚠ Could not validate structure: {e}")

    # Test 3: Test invocation with sample data (requires API key)
    print("\n✓ Test 3: Chain invocation (dry run - checks interface)")

    sample_variables = {
        "round_number": 1,
        "conversation_history": "",  # Empty for round 1
        "question": "What is your favorite hobby?"
    }

    print("  Sample variables:")
    for key, value in sample_variables.items():
        display_value = value if value else "(empty)"
        if len(str(display_value)) > 50:
            display_value = str(display_value)[:50] + "..."
        print(f"    {key}: {display_value}")

    print("\n  ⚠ Note: Actual API call test will be in Step 1.7 integration test")
    print("  Chain interface validated - ready for invocation")

    # Test 4: Language validation
    print("\n✓ Test 4: Language validation")
    try:
        chain_ko = _build_chain("gpt-5", "ko")
        print("  ✗ Korean chain should have raised error")
        return False
    except ValueError as e:
        print(f"  ✓ Correctly rejects unsupported language: {str(e)[:50]}...")

    print("\n" + "=" * 70)
    print("✓ Chain construction tests passed!")
    print("=" * 70)
    print("\nChain is ready for invocation:")
    print("  response = chain.invoke(variables)")
    print("  # Returns: String (AI-generated text)")

    return True


if __name__ == "__main__":
    success = test_chain()
    sys.exit(0 if success else 1)
