"""
Test script for game result archival to Firestore.

This creates mock game data and tests the _archive_game_result() function
to verify it correctly writes to the game_results collection.

Usage:
    uv run python test_game_archival.py
"""

# Load environment variables first (before importing app modules)
from app.core import config

import sys
import uuid
from datetime import datetime, timezone, timedelta
from app.services.firebase_service import get_firestore_client
from app.services.game_service import _archive_game_result
from firebase_admin import firestore


def create_mock_game_data():
    """
    Creates realistic mock game data that simulates a finished game.

    Returns:
        Tuple of (game_ref, game_data, winner)
    """
    db = get_firestore_client()

    # Create a test game document
    test_game_id = f"test_game_{uuid.uuid4().hex[:8]}"
    game_ref = db.collection("game_rooms").document(test_game_id)

    # Mock player data
    human_uid = f"human_{uuid.uuid4().hex[:8]}"
    ai_uid = f"ai_{uuid.uuid4().hex[:8]}"

    players = [
        {
            "uid": human_uid,
            "gameDisplayName": "TestHuman",
            "isImpostor": False,
            "isEliminated": False
        },
        {
            "uid": ai_uid,
            "gameDisplayName": "TestAI",
            "isImpostor": True,
            "isEliminated": True  # AI was eliminated, humans win
        }
    ]

    # Mock rounds data
    rounds = [
        {
            "round": 1,
            "question": "What is your favorite food?"
        },
        {
            "round": 2,
            "question": "What did you do last weekend?"
        }
    ]

    # Mock votes data
    votes = [
        {
            "voterId": human_uid,
            "targetId": ai_uid,
            "round": 2
        }
    ]

    # Mock game data structure (what tally_votes sees)
    game_data = {
        "gameId": test_game_id,
        "language": "en",
        "aiModelId": "gpt-5-test",
        "currentRound": 2,
        "status": "finished",
        "players": players,
        "rounds": rounds,
        "votes": votes,
        "lastRoundResult": {
            "eliminatedPlayerId": ai_uid,
            "endReason": "All impostors have been eliminated. Humans win!",
            "voteCounts": {ai_uid: 1}
        }
    }

    # Write mock game to Firestore
    game_ref.set(game_data)

    # Create mock messages in subcollection
    messages_ref = game_ref.collection("messages")

    # Round 1 messages
    messages_ref.add({
        "senderId": human_uid,
        "senderName": "TestHuman",
        "text": "Pizza is my favorite!",
        "roundNumber": 1,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

    messages_ref.add({
        "senderId": ai_uid,
        "senderName": "TestAI",
        "text": "I really enjoy sushi.",
        "roundNumber": 1,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

    # Round 2 messages
    messages_ref.add({
        "senderId": human_uid,
        "senderName": "TestHuman",
        "text": "I went hiking with friends.",
        "roundNumber": 2,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

    messages_ref.add({
        "senderId": ai_uid,
        "senderName": "TestAI",
        "text": "I relaxed and read books.",
        "roundNumber": 2,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

    winner = "humans"

    return game_ref, game_data, winner


def verify_game_result(game_id: str):
    """
    Verifies that game result was written correctly to game_results collection.

    Args:
        game_id: The game ID to look for in game_results

    Returns:
        bool: True if verification passed, False otherwise
    """
    db = get_firestore_client()

    # Query game_results for this game
    results = db.collection("game_results").where("gameId", "==", game_id).limit(1).stream()

    result_docs = list(results)
    if not result_docs:
        print(f"❌ FAIL: No game result found for gameId={game_id}")
        return False

    result_data = result_docs[0].to_dict()

    # Verify required fields
    required_fields = ["gameId", "endedAt", "language", "aiModelUsed", "winner", "totalRounds"]
    missing_fields = [f for f in required_fields if f not in result_data]

    if missing_fields:
        print(f"❌ FAIL: Missing required fields: {missing_fields}")
        return False

    # Verify nested arrays
    if "players" not in result_data or len(result_data["players"]) != 2:
        print(f"❌ FAIL: Expected 2 players, got {len(result_data.get('players', []))}")
        return False

    if "rounds" not in result_data or len(result_data["rounds"]) != 2:
        print(f"❌ FAIL: Expected 2 rounds, got {len(result_data.get('rounds', []))}")
        return False

    if "votes" not in result_data or len(result_data["votes"]) != 1:
        print(f"❌ FAIL: Expected 1 vote, got {len(result_data.get('votes', []))}")
        return False

    # Verify round structure
    for round_data in result_data["rounds"]:
        if "revealedAnswers" not in round_data:
            print(f"❌ FAIL: Round {round_data.get('roundNumber')} missing revealedAnswers")
            return False

        if len(round_data["revealedAnswers"]) != 2:
            print(f"❌ FAIL: Round {round_data.get('roundNumber')} should have 2 answers")
            return False

        # Verify isAI flag exists on answers
        for answer in round_data["revealedAnswers"]:
            if "isAI" not in answer:
                print(f"❌ FAIL: Answer missing isAI flag")
                return False

    # Verify winner
    if result_data["winner"] != "humans":
        print(f"❌ FAIL: Expected winner='humans', got '{result_data['winner']}'")
        return False

    # Verify AI model
    if result_data["aiModelUsed"] != "gpt-5-test":
        print(f"❌ FAIL: Expected aiModelUsed='gpt-5-test', got '{result_data['aiModelUsed']}'")
        return False

    print("\n✅ ALL VERIFICATIONS PASSED!")
    print("\n📊 Game Result Summary:")
    print(f"   Game ID: {result_data['gameId']}")
    print(f"   Language: {result_data['language']}")
    print(f"   AI Model: {result_data['aiModelUsed']}")
    print(f"   Winner: {result_data['winner']}")
    print(f"   Total Rounds: {result_data['totalRounds']}")
    print(f"   Players: {len(result_data['players'])}")
    print(f"   Votes: {len(result_data['votes'])}")
    print(f"   Rounds with answers: {len(result_data['rounds'])}")

    # Print round details
    for round_data in result_data["rounds"]:
        print(f"\n   Round {round_data['roundNumber']}: {round_data['question']}")
        for answer in round_data["revealedAnswers"]:
            ai_flag = "🤖" if answer["isAI"] else "👤"
            print(f"     {ai_flag} {answer['playerName']}: {answer['text']}")

    return True


def cleanup_test_data(game_id: str):
    """
    Removes test data from Firestore.

    Args:
        game_id: The test game ID to clean up
    """
    db = get_firestore_client()

    # Delete game_rooms document and subcollections
    game_ref = db.collection("game_rooms").document(game_id)

    # Delete messages subcollection
    messages = game_ref.collection("messages").stream()
    for msg in messages:
        msg.reference.delete()

    # Delete game document
    game_ref.delete()

    # Delete game_results document
    results = db.collection("game_results").where("gameId", "==", game_id).stream()
    for result in results:
        result.reference.delete()

    print(f"\n🧹 Cleaned up test data for game {game_id}")


def main():
    """Main test execution."""
    print("=" * 70)
    print("GAME RESULT ARCHIVAL TEST")
    print("=" * 70)

    try:
        # Step 1: Create mock game data
        print("\n📝 Step 1: Creating mock game data...")
        game_ref, game_data, winner = create_mock_game_data()
        game_id = game_ref.id
        print(f"   ✓ Created test game: {game_id}")

        # Step 2: Call archival function
        print("\n📤 Step 2: Calling _archive_game_result()...")
        _archive_game_result(game_ref, game_data, winner)
        print("   ✓ Archive function executed")

        # Give Firestore a moment to process
        import time
        time.sleep(2)

        # Step 3: Verify result
        print("\n🔍 Step 3: Verifying game_results document...")
        success = verify_game_result(game_id)

        if success:
            print("\n" + "=" * 70)
            print("✅ TEST PASSED - Game archival working correctly!")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("❌ TEST FAILED - See errors above")
            print("=" * 70)
            sys.exit(1)

        # Step 4: Cleanup
        try:
            cleanup_input = input("\n🗑️  Delete test data? (y/n): ").strip().lower()
            if cleanup_input == 'y':
                cleanup_test_data(game_id)
            else:
                print(f"\n⚠️  Test data retained. Manual cleanup required for game: {game_id}")
        except EOFError:
            # Non-interactive mode - auto-cleanup
            print("\n🗑️  Non-interactive mode: Auto-cleaning test data...")
            cleanup_test_data(game_id)

    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
