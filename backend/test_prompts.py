"""Verification script for Step 1.4: Prompt templates.

Run this from the backend directory to verify prompt rendering:
    uv run test_prompts.py
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ai_service import (
    _format_conversation_history,
    _create_prompt_template,
    SYSTEM_PROMPT_EN,
    USER_PROMPT_EN,
)


def test_prompts():
    """Test prompt template creation and rendering."""
    print("=" * 70)
    print("Step 1.4 Verification: Prompt Templates")
    print("=" * 70)

    # Test 1: Conversation history formatting
    print("\n✓ Test 1: Conversation history formatting")

    # Empty history (round 1)
    empty_history = []
    formatted_empty = _format_conversation_history(empty_history)
    print(f"  Empty history result: '{formatted_empty}' (should be empty string)")
    assert formatted_empty == "", "Empty history should return empty string"

    # With history (round 2+)
    sample_history = [
        {
            "round": 1,
            "question": "What is your favorite weekend activity?",
            "your_answer": "I love hiking when the weather's nice, but honestly most weekends I just binge Netflix and order takeout."
        },
        {
            "round": 2,
            "question": "Describe your ideal vacation destination.",
            "your_answer": "Probably somewhere with mountains and good food. Switzerland maybe? But realistically anywhere with wifi works."
        }
    ]
    formatted_history = _format_conversation_history(sample_history)
    print(f"\n  Formatted history (2 rounds):")
    print("  " + "\n  ".join(formatted_history.split("\n")))

    # Test 2: Template creation
    print("\n✓ Test 2: Template creation")
    try:
        template = _create_prompt_template("en")
        print(f"  English template created: {type(template).__name__}")
    except Exception as e:
        print(f"  ✗ Error creating template: {e}")
        return False

    # Test Korean (should fail gracefully)
    try:
        template_ko = _create_prompt_template("ko")
        print(f"  ✗ Korean template should have failed but didn't")
        return False
    except ValueError as e:
        print(f"  ✓ Korean template correctly raises error: {str(e)[:50]}...")

    # Test 3: Prompt rendering (Round 1, no history)
    print("\n✓ Test 3: Prompt rendering - Round 1 (no history)")
    prompt_vars_round1 = {
        "nickname": "Silent Wolf",
        "round_number": 1,
        "conversation_history": "",
        "question": "What is your favorite hobby?"
    }

    messages_round1 = template.format_messages(**prompt_vars_round1)
    print(f"\n  Number of messages: {len(messages_round1)}")
    print(f"  Message types: {[msg.type for msg in messages_round1]}")

    print("\n  --- SYSTEM MESSAGE ---")
    print("  " + "\n  ".join(messages_round1[0].content.split("\n")[:5]))
    print("  ...")

    print("\n  --- USER MESSAGE ---")
    print("  " + "\n  ".join(messages_round1[1].content.split("\n")))

    # Test 4: Prompt rendering (Round 3, with history)
    print("\n✓ Test 4: Prompt rendering - Round 3 (with history)")
    prompt_vars_round3 = {
        "nickname": "Silent Wolf",
        "round_number": 3,
        "conversation_history": formatted_history,
        "question": "What was the last book you enjoyed reading?"
    }

    messages_round3 = template.format_messages(**prompt_vars_round3)

    print("\n  --- USER MESSAGE (with history) ---")
    user_content = messages_round3[1].content
    # Show first 10 lines
    lines = user_content.split("\n")
    for line in lines[:15]:
        print(f"  {line}")
    if len(lines) > 15:
        print(f"  ... ({len(lines) - 15} more lines)")

    # Test 5: Variable injection
    print("\n✓ Test 5: Variable injection verification")
    system_content = messages_round3[0].content

    checks = [
        ("Nickname injected", "Silent Wolf" in system_content),
        ("Round number injected", "round 3" in system_content),
        ("Question in user prompt", "What was the last book" in user_content),
        ("History in user prompt", "Previous rounds:" in user_content),
    ]

    for check_name, check_result in checks:
        status = "✓" if check_result else "✗"
        print(f"  {status} {check_name}")
        if not check_result:
            return False

    print("\n" + "=" * 70)
    print("✓ All prompt tests passed! Templates are working correctly.")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_prompts()
    sys.exit(0 if success else 1)
