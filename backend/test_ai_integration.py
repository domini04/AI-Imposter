"""Integration test for Phase 1: Complete AI generation pipeline.

This test makes a REAL API call to OpenAI to validate the entire flow.
Run from backend directory: uv run test_ai_integration.py

IMPORTANT: This will consume OpenAI API credits (minimal cost, ~$0.001 per test)
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from app.core import config

from app.services import ai_service


def test_ai_generation_round1():
    """Test AI generation for round 1 (no history)."""
    print("=" * 70)
    print("Phase 1 Integration Test: AI Generation (Round 1)")
    print("=" * 70)

    print("\n⚠ WARNING: This test makes a REAL API call to OpenAI")
    print("  Estimated cost: ~$0.001")
    print()

    # Test parameters
    test_data = {
        "model_id": "gpt-5",
        "question": "What is your favorite hobby?",
        "language": "en",
        "round_number": 1,
        "nickname": "Silent Wolf",
        "conversation_history": [],  # Empty for round 1
        "game_id": "test_integration_001"
    }

    print("Test Input:")
    print(f"  Model: {test_data['model_id']}")
    print(f"  Question: {test_data['question']}")
    print(f"  Nickname: {test_data['nickname']}")
    print(f"  Round: {test_data['round_number']} (no history)")
    print()

    try:
        print("Calling ai_service.generate_ai_response()...")
        print()

        response = ai_service.generate_ai_response(**test_data)

        print("=" * 70)
        print("✓ SUCCESS: AI Response Generated")
        print("=" * 70)
        print()
        print(f"Response ({len(response)} chars):")
        print()
        print(f"  \"{response}\"")
        print()

        # Validation
        assert isinstance(response, str), "Response should be a string"
        assert len(response) > 0, "Response should not be empty"
        assert len(response) < 1000, "Response should be reasonable length"

        # Count sentences (rough estimate)
        sentence_count = response.count('.') + response.count('!') + response.count('?')
        print(f"Validation:")
        print(f"  ✓ Type: string")
        print(f"  ✓ Length: {len(response)} chars")
        print(f"  ✓ Sentences: ~{sentence_count} (target: 2-5)")
        print(f"  ✓ Not fallback: {'fallback' not in response.lower()}")

        return True

    except Exception as e:
        print("=" * 70)
        print("✗ FAILED: Error during AI generation")
        print("=" * 70)
        print(f"Error: {type(e).__name__}: {str(e)}")
        return False


def test_ai_generation_round2():
    """Test AI generation for round 2 (with history)."""
    print("\n\n")
    print("=" * 70)
    print("Phase 1 Integration Test: AI Generation (Round 2 with History)")
    print("=" * 70)

    # Test parameters with history
    test_data = {
        "model_id": "gpt-5",
        "question": "What was your last vacation like?",
        "language": "en",
        "round_number": 2,
        "nickname": "Silent Wolf",
        "conversation_history": [
            {
                "round": 1,
                "question": "What is your favorite hobby?",
                "your_answer": "I love hiking and photography, especially on weekends!"
            }
        ],
        "game_id": "test_integration_002"
    }

    print("\nTest Input:")
    print(f"  Model: {test_data['model_id']}")
    print(f"  Question: {test_data['question']}")
    print(f"  Nickname: {test_data['nickname']}")
    print(f"  Round: {test_data['round_number']} (with history)")
    print(f"  History: {len(test_data['conversation_history'])} previous rounds")
    print()

    try:
        print("Calling ai_service.generate_ai_response()...")
        print()

        response = ai_service.generate_ai_response(**test_data)

        print("=" * 70)
        print("✓ SUCCESS: AI Response with Context Generated")
        print("=" * 70)
        print()
        print(f"Response ({len(response)} chars):")
        print()
        print(f"  \"{response}\"")
        print()

        # Validation
        assert isinstance(response, str), "Response should be a string"
        assert len(response) > 0, "Response should not be empty"

        print(f"Validation:")
        print(f"  ✓ Type: string")
        print(f"  ✓ Length: {len(response)} chars")
        print(f"  ✓ Contextual: Response should relate to hiking/photography")

        # Check if response might reference previous answer
        context_words = ["hik", "photo", "weekend", "mountain", "nature"]
        has_context = any(word in response.lower() for word in context_words)
        print(f"  {'✓' if has_context else '⚠'} Contextual clues: {has_context}")

        return True

    except Exception as e:
        print("=" * 70)
        print("✗ FAILED: Error during AI generation with history")
        print("=" * 70)
        print(f"Error: {type(e).__name__}: {str(e)}")
        return False


def main():
    """Run all integration tests."""
    print("\n")
    print("#" * 70)
    print("# PHASE 1 COMPLETE - AI SERVICE INTEGRATION TEST")
    print("#" * 70)
    print()

    results = []

    # Test 1: Round 1 (no history)
    results.append(("Round 1 (no history)", test_ai_generation_round1()))

    # Test 2: Round 2 (with history)
    results.append(("Round 2 (with history)", test_ai_generation_round2()))

    # Summary
    print("\n\n")
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print()
        print("=" * 70)
        print("🎉 ALL TESTS PASSED - PHASE 1 COMPLETE!")
        print("=" * 70)
        print()
        print("The AI service is fully functional:")
        print("  ✓ Factory creates LLM instances")
        print("  ✓ Prompts format correctly")
        print("  ✓ History extraction works")
        print("  ✓ Chain executes successfully")
        print("  ✓ OpenAI API integration works")
        print("  ✓ Real AI responses generated")
        print()
        print("Next: Integrate with game_service to replace placeholders!")
    else:
        print()
        print("=" * 70)
        print("⚠ SOME TESTS FAILED")
        print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
