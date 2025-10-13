"""Verification script for Step 1.5: Conversation history extraction.

This tests the logic without requiring actual Firestore access.
Run from backend directory: uv run test_history_extraction.py
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import after path setup
from app.services.game_service import _extract_ai_conversation_history


def create_mock_game_ref(rounds_data, messages_data):
    """Create a mock Firestore game reference with test data."""
    game_ref = Mock()
    game_ref.id = "test_game_123"

    # Mock game document get()
    game_doc = Mock()
    game_doc.to_dict.return_value = {
        "rounds": rounds_data,
        "currentRound": 3
    }
    game_ref.get.return_value = game_doc

    # Mock messages subcollection
    messages_collection = Mock()

    # Mock query chain
    query_mock = Mock()
    query_mock.where = Mock(return_value=query_mock)
    query_mock.order_by = Mock(return_value=query_mock)

    # Mock message documents
    mock_messages = []
    for msg in messages_data:
        msg_doc = Mock()
        msg_doc.id = msg.get("id", "msg_123")
        msg_doc.to_dict.return_value = msg
        mock_messages.append(msg_doc)

    query_mock.stream.return_value = iter(mock_messages)

    messages_collection.where.return_value = query_mock
    game_ref.collection.return_value = messages_collection

    return game_ref


def test_history_extraction():
    """Test conversation history extraction with various scenarios."""
    print("=" * 70)
    print("Step 1.5 Verification: Conversation History Extraction")
    print("=" * 70)

    # Test 1: Round 1 (no history)
    print("\n✓ Test 1: Round 1 - Should return empty list")
    game_ref = create_mock_game_ref([], [])
    history = _extract_ai_conversation_history(game_ref, "ai_123", 1)
    assert history == [], f"Expected empty list, got {history}"
    print(f"  Result: {history} (correct)")

    # Test 2: Round 2 with one previous message
    print("\n✓ Test 2: Round 2 - One message in history")
    rounds = [
        {"round": 1, "question": "What is your favorite hobby?"},
        {"round": 2, "question": "What was your last vacation?"}
    ]
    messages = [
        {
            "id": "msg_001",
            "senderId": "ai_123",
            "roundNumber": 1,
            "text": "I love hiking and photography, especially on weekends!"
        }
    ]
    game_ref = create_mock_game_ref(rounds, messages)
    history = _extract_ai_conversation_history(game_ref, "ai_123", 2)

    print(f"  Found {len(history)} history entries")
    assert len(history) == 1, f"Expected 1 entry, got {len(history)}"
    assert history[0]["round"] == 1
    assert history[0]["question"] == "What is your favorite hobby?"
    assert "hiking" in history[0]["your_answer"]
    print(f"  Round: {history[0]['round']}")
    print(f"  Question: {history[0]['question'][:50]}...")
    print(f"  Answer: {history[0]['your_answer'][:50]}...")

    # Test 3: Round 3 with two previous messages
    print("\n✓ Test 3: Round 3 - Two messages in history")
    rounds = [
        {"round": 1, "question": "What is your favorite hobby?"},
        {"round": 2, "question": "What was your last vacation?"},
        {"round": 3, "question": "What book do you recommend?"}
    ]
    messages = [
        {
            "id": "msg_001",
            "senderId": "ai_123",
            "roundNumber": 1,
            "text": "I love hiking and photography!"
        },
        {
            "id": "msg_002",
            "senderId": "ai_123",
            "roundNumber": 2,
            "text": "I went to the mountains last summer. Beautiful views!"
        }
    ]
    game_ref = create_mock_game_ref(rounds, messages)
    history = _extract_ai_conversation_history(game_ref, "ai_123", 3)

    print(f"  Found {len(history)} history entries")
    assert len(history) == 2, f"Expected 2 entries, got {len(history)}"
    assert history[0]["round"] == 1
    assert history[1]["round"] == 2
    assert "hiking" in history[0]["your_answer"]
    assert "mountains" in history[1]["your_answer"]
    print(f"  ✓ Both rounds present and in order")

    # Test 4: Missing message for a round (graceful degradation)
    print("\n✓ Test 4: Missing message (graceful degradation)")
    rounds = [
        {"round": 1, "question": "Question 1"},
        {"round": 2, "question": "Question 2"},
        {"round": 3, "question": "Question 3"}
    ]
    # Only round 1 message, round 2 is missing
    messages = [
        {
            "id": "msg_001",
            "senderId": "ai_123",
            "roundNumber": 1,
            "text": "Answer to question 1"
        }
    ]
    game_ref = create_mock_game_ref(rounds, messages)
    history = _extract_ai_conversation_history(game_ref, "ai_123", 3)

    print(f"  Found {len(history)} history entries (expected 1, round 2 missing)")
    assert len(history) == 1, f"Expected 1 entry, got {len(history)}"
    assert history[0]["round"] == 1
    print(f"  ✓ Continues with partial history (logged warning in real execution)")

    # Test 5: Malformed message (missing fields)
    print("\n✓ Test 5: Malformed message - missing roundNumber")
    rounds = [
        {"round": 1, "question": "Question 1"},
        {"round": 2, "question": "Question 2"}
    ]
    messages = [
        {
            "id": "msg_bad",
            "senderId": "ai_123",
            # Missing roundNumber!
            "text": "This message is malformed"
        }
    ]
    game_ref = create_mock_game_ref(rounds, messages)
    history = _extract_ai_conversation_history(game_ref, "ai_123", 2)

    print(f"  Found {len(history)} history entries (malformed message skipped)")
    assert len(history) == 0, f"Expected 0 entries, got {len(history)}"
    print(f"  ✓ Skips malformed messages gracefully")

    # Test 6: Data structure validation
    print("\n✓ Test 6: Output data structure validation")
    rounds = [{"round": 1, "question": "Test Q"}]
    messages = [{
        "id": "msg_001",
        "senderId": "ai_123",
        "roundNumber": 1,
        "text": "Test A"
    }]
    game_ref = create_mock_game_ref(rounds, messages)
    history = _extract_ai_conversation_history(game_ref, "ai_123", 2)

    assert isinstance(history, list), "History should be a list"
    assert isinstance(history[0], dict), "Each entry should be a dict"
    assert "round" in history[0], "Entry missing 'round' key"
    assert "question" in history[0], "Entry missing 'question' key"
    assert "your_answer" in history[0], "Entry missing 'your_answer' key"
    assert isinstance(history[0]["round"], int), "'round' should be int"
    assert isinstance(history[0]["question"], str), "'question' should be str"
    assert isinstance(history[0]["your_answer"], str), "'your_answer' should be str"
    print(f"  ✓ Output structure matches ai_service expectations")

    print("\n" + "=" * 70)
    print("✓ All history extraction tests passed!")
    print("=" * 70)
    print("\nKey Features Verified:")
    print("  ✓ Returns empty list for round 1")
    print("  ✓ Extracts messages from previous rounds only")
    print("  ✓ Structures data correctly for AI service")
    print("  ✓ Gracefully handles missing messages")
    print("  ✓ Skips malformed data with warnings")
    print("  ✓ Maintains round order")
    return True


if __name__ == "__main__":
    success = test_history_extraction()
    sys.exit(0 if success else 1)
