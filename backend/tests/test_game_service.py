import pytest
from unittest.mock import MagicMock, patch
from app.services import game_service
from app.models.game import CreateGameRequest
from datetime import datetime, timezone, timedelta

# We use a patch to replace the actual firestore client with a mock
# during the entire test session for this file.
@pytest.fixture(autouse=True)
def mock_firestore_client():
    """
    Replaces the get_firestore_client dependency with a mock,
    allowing us to simulate Firestore behavior without a real connection.
    """
    with patch('app.services.game_service.get_firestore_client') as mock_client:
        # We create a mock for the chain of calls like db.collection().document().get()
        mock_db = MagicMock()
        mock_client.return_value = mock_db
        yield mock_db

def test_create_game_successfully(mock_firestore_client):
    """
    Tests that create_game function correctly structures the game data
    and calls the firestore client to add a new document.
    """
    # Arrange
    host_uid = "test_host_123"
    settings = CreateGameRequest(
        language="en", # FIX: Use the shortcode as required by the model
        aiCount=1,
        privacy="public"
    )
    
    # Mock the return value of the .add() call to simulate a Firestore response
    mock_game_ref = MagicMock()
    mock_game_ref.id = "new_game_abc"
    mock_firestore_client.collection.return_value.add.return_value = (None, mock_game_ref)

    # Act
    game_id = game_service.create_game(host_uid, settings)

    # Assert
    assert game_id == "new_game_abc"
    
    # Check that the .add() method was called exactly once
    mock_firestore_client.collection.return_value.add.assert_called_once()
    
    # Grab the arguments passed to .add() and verify them
    added_data = mock_firestore_client.collection.return_value.add.call_args[0][0]
    
    assert added_data['hostId'] == host_uid
    assert added_data['language'] == "en"
    assert added_data['aiCount'] == 1
    assert added_data['status'] == "waiting"
    assert len(added_data['players']) == 1
    assert added_data['players'][0]['uid'] == host_uid

def test_list_public_games_returns_formatted_list(mock_firestore_client):
    """
    Tests that list_public_games returns a correctly formatted list of games
    when public games are available.
    """
    # Arrange
    mock_game_1 = MagicMock()
    mock_game_1.id = "game_1"
    mock_game_1.to_dict.return_value = {
        "language": "English",
        "players": [{}, {}] # 2 players
    }
    
    mock_game_2 = MagicMock()
    mock_game_2.id = "game_2"
    mock_game_2.to_dict.return_value = {
        "language": "Korean",
        "players": [{}] # 1 player
    }
    
    # Simulate the query.stream() returning our two mock games
    mock_firestore_client.collection.return_value.where.return_value.where.return_value.stream.return_value = [mock_game_1, mock_game_2]
    
    # Act
    public_games = game_service.list_public_games()
    
    # Assert
    assert len(public_games) == 2
    assert public_games[0]['gameId'] == "game_1"
    assert public_games[0]['playerCount'] == 2
    assert public_games[1]['gameId'] == "game_2"
    assert public_games[1]['playerCount'] == 1
    assert public_games[1]['language'] == "Korean"

def test_list_public_games_returns_empty_list_when_no_games(mock_firestore_client):
    """
    Tests that list_public_games returns an empty list when the query
    finds no matching games.
    """
    # Arrange
    # Simulate the query.stream() returning an empty list
    mock_firestore_client.collection.return_value.where.return_value.where.return_value.stream.return_value = []
    
    # Act
    public_games = game_service.list_public_games()
    
    # Assert
    assert public_games == []

def test_join_game_successfully(mock_firestore_client):
    """
    Tests that a player can successfully join a valid game.
    """
    # Arrange
    mock_game_doc = MagicMock()
    mock_game_doc.exists = True
    mock_game_doc.to_dict.return_value = {
        "status": "waiting",
        "players": [{"uid": "player1"}] # One player already in game
    }
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_game_doc
    
    # Act
    game_service.join_game("valid_game", "player2")
    
    # Assert
    # Verify that .update() was called to add the new player
    update_call = mock_firestore_client.collection.return_value.document.return_value.update
    update_call.assert_called_once()
    
    # FIX: Inspect the ArrayUnion object directly instead of converting to string
    array_union_arg = update_call.call_args[0][0]['players']
    new_player_data = array_union_arg.values[0]
    assert new_player_data['uid'] == 'player2'


@pytest.mark.parametrize("game_data, expected_error", [
    (None, "Game not found."), # Simulate game_doc.exists = False
    ({"status": "in_progress", "players": []}, "This game is not waiting for players."),
    ({"status": "waiting", "players": [{}, {}, {}, {}]}, "This game is full."),
    ({"status": "waiting", "players": [{"uid": "player1"}]}, "You have already joined this game."),
])
def test_join_game_failures(mock_firestore_client, game_data, expected_error):
    """
    Tests that join_game raises ValueError for various invalid conditions.
    """
    # Arrange
    mock_game_doc = MagicMock()
    if game_data is None:
        mock_game_doc.exists = False
    else:
        mock_game_doc.exists = True
        mock_game_doc.to_dict.return_value = game_data
        
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_game_doc

    # Act & Assert
    with pytest.raises(ValueError, match=expected_error):
        # player1 is the user trying to join in the parametrized tests
        game_service.join_game("any_game", "player1")

def test_start_game_successfully(mock_firestore_client):
    """
    Tests that a host can start a game, which assigns impostors,
    shuffles players, and updates the game state.
    """
    # Arrange
    host_uid = "host1"
    initial_players = [{"uid": host_uid}, {"uid": "player2"}]
    mock_game_doc = MagicMock()
    mock_game_doc.exists = True
    mock_game_doc.to_dict.return_value = {
        "status": "waiting",
        "hostId": host_uid,
        "players": initial_players,
        "aiCount": 1
    }
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_game_doc

    # Act
    game_service.start_game("any_game", host_uid)

    # Assert
    update_call = mock_firestore_client.collection.return_value.document.return_value.update
    update_call.assert_called_once()
    
    updated_data = update_call.call_args[0][0]
    final_players = updated_data['players']

    assert updated_data['status'] == "in_progress"
    assert updated_data['currentRound'] == 1
    assert len(final_players) == 3 # 2 humans + 1 AI
    
    # Check that exactly one player is the impostor
    impostor_count = sum(1 for p in final_players if p.get('isImpostor'))
    assert impostor_count == 1

@pytest.mark.parametrize("game_data, user_id, expected_error", [
    ({"status": "waiting", "hostId": "host1"}, "not_host", "Only the host can start the game."),
    ({"status": "in_progress", "hostId": "host1"}, "host1", "The game has already started or is finished."),
])
def test_start_game_failures(mock_firestore_client, game_data, user_id, expected_error):
    """
    Tests that start_game raises ValueError for invalid conditions.
    """
    # Arrange
    mock_game_doc = MagicMock()
    mock_game_doc.exists = True
    mock_game_doc.to_dict.return_value = game_data
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_game_doc

    # Act & Assert
    with pytest.raises(ValueError, match=expected_error):
        game_service.start_game("any_game", user_id)

def test_submit_answer_successfully(mock_firestore_client):
    """
    Tests that a player can successfully submit an answer.
    """
    # Arrange
    user_uid = "player1"
    mock_game_doc = MagicMock()
    mock_game_doc.exists = True
    mock_game_doc.to_dict.return_value = {
        "status": "in_progress",
        "roundPhase": "ANSWER_SUBMISSION",
        "players": [{"uid": user_uid}]
    }
    # Mock the subcollection query to show no existing answer
    mock_pending_messages_ref = MagicMock()
    mock_pending_messages_ref.where.return_value.limit.return_value.get.return_value = []
    
    mock_game_ref = mock_firestore_client.collection.return_value.document.return_value
    mock_game_ref.get.return_value = mock_game_doc
    mock_game_ref.collection.return_value = mock_pending_messages_ref
    
    # Act
    game_service.submit_answer("any_game", user_uid, "my test answer")
    
    # Assert
    mock_pending_messages_ref.add.assert_called_once()
    added_answer = mock_pending_messages_ref.add.call_args[0][0]
    
    assert added_answer['authorId'] == user_uid
    assert added_answer['content'] == "my test answer"


@pytest.mark.parametrize("game_data, has_existing_answer, expected_error", [
    ({"status": "waiting", "roundPhase": "ANSWER_SUBMISSION", "players": [{"uid": "p1"}]}, False, "This game is not currently in progress."),
    ({"status": "in_progress", "roundPhase": "VOTING", "players": [{"uid": "p1"}]}, False, "It is not currently time to submit answers."),
    ({"status": "in_progress", "roundPhase": "ANSWER_SUBMISSION", "players": [{"uid": "p2"}]}, False, "You are not a player in this game."),
    ({"status": "in_progress", "roundPhase": "ANSWER_SUBMISSION", "players": [{"uid": "p1"}]}, True, "You have already submitted an answer for this round."),
])
def test_submit_answer_failures(mock_firestore_client, game_data, has_existing_answer, expected_error):
    """
    Tests that submit_answer raises ValueError for various invalid conditions.
    """
    # Arrange
    user_uid = "p1"
    mock_game_doc = MagicMock()
    mock_game_doc.exists = True
    mock_game_doc.to_dict.return_value = game_data

    # Mock the subcollection query for existing answers
    mock_pending_messages_ref = MagicMock()
    existing_answer = [MagicMock()] if has_existing_answer else []
    mock_pending_messages_ref.where.return_value.limit.return_value.get.return_value = existing_answer
    
    mock_game_ref = mock_firestore_client.collection.return_value.document.return_value
    mock_game_ref.get.return_value = mock_game_doc
    mock_game_ref.collection.return_value = mock_pending_messages_ref
    
    # Act & Assert
    with pytest.raises(ValueError, match=expected_error):
        game_service.submit_answer("any_game", user_uid, "any answer")

def test_tally_answers_successfully(mock_firestore_client, mocker):
    """
    Tests that tally_answers moves messages and updates the game state
    when called correctly after the timer has expired.
    """
    # Arrange
    now = datetime.now(timezone.utc)
    # Patching datetime.now() to control time for the test
    mocker.patch('app.services.game_service.datetime.datetime', mocker.Mock(now=lambda tz: now))
    
    # Simulate a round that ended 1 second ago
    round_end_time = now - timedelta(seconds=1)

    mock_game_doc = MagicMock()
    mock_game_doc.exists = True
    mock_game_doc.to_dict.return_value = {
        "status": "in_progress",
        "roundPhase": "ANSWER_SUBMISSION",
        "roundEndTime": round_end_time
    }

    mock_msg1 = MagicMock()
    mock_msg1.id = "msg1"
    mock_msg1.to_dict.return_value = {"content": "answer 1"}
    
    mock_transaction = mock_firestore_client.transaction.return_value
    
    game_ref = mock_firestore_client.collection.return_value.document.return_value
    game_ref.get.return_value = mock_game_doc
    
    pending_messages_ref = game_ref.collection.return_value
    pending_messages_ref.stream.return_value = [mock_msg1]

    # Act
    game_service.tally_answers("any_game")

    # Assert
    # Check that the main game document was updated correctly
    transaction_update_args = mock_transaction.update.call_args[0][1]
    assert transaction_update_args['roundPhase'] == "VOTING"
    assert transaction_update_args['roundEndTime'] > now

    # Check that the message was moved (set and then deleted)
    assert mock_transaction.set.call_count == 1
    assert mock_transaction.delete.call_count == 1
    
@pytest.mark.parametrize("game_data, time_offset_seconds, expected_error", [
    ({"status": "waiting", "roundPhase": "ANSWER_SUBMISSION"}, -1, "This game is not currently in progress."),
    ({"status": "in_progress", "roundPhase": "VOTING"}, -1, None), # Should be idempotent
    ({"status": "in_progress", "roundPhase": "ANSWER_SUBMISSION"}, 10, "Answer submission time has not ended yet."),
])
def test_tally_answers_failures_and_idempotency(mock_firestore_client, mocker, game_data, time_offset_seconds, expected_error):
    # Arrange
    now = datetime.now(timezone.utc)
    mocker.patch('app.services.game_service.datetime.datetime', mocker.Mock(now=lambda tz: now))
    
    round_end_time = now + timedelta(seconds=time_offset_seconds)
    full_game_data = {**game_data, "roundEndTime": round_end_time}

    mock_game_doc = MagicMock()
    mock_game_doc.exists = True
    mock_game_doc.to_dict.return_value = full_game_data
    
    game_ref = mock_firestore_client.collection.return_value.document.return_value
    game_ref.get.return_value = mock_game_doc
    
    # Act & Assert
    if expected_error:
        with pytest.raises(ValueError, match=expected_error):
            game_service.tally_answers("any_game")
    else:
        # This is for the idempotency test, where no error should be raised
        game_service.tally_answers("any_game")
        mock_transaction = mock_firestore_client.transaction.return_value
        mock_transaction.update.assert_not_called()

def test_submit_vote_successfully(mock_firestore_client):
    """
    Tests that a player can successfully cast a valid vote.
    """
    # Arrange
    voter_uid = "player1"
    target_uid = "player2"
    mock_game_doc = MagicMock()
    mock_game_doc.exists = True
    mock_game_doc.to_dict.return_value = {
        "status": "in_progress",
        "roundPhase": "VOTING",
        "currentRound": 2,
        "players": [{"uid": voter_uid}, {"uid": target_uid}],
        "votes": [] # No previous votes
    }
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_game_doc

    # Act
    game_service.submit_vote("any_game", voter_uid, target_uid)

    # Assert
    update_call = mock_firestore_client.collection.return_value.document.return_value.update
    update_call.assert_called_once()
    
    array_union_arg = update_call.call_args[0][0]['votes']
    new_vote_data = array_union_arg.values[0]
    
    assert new_vote_data['voterId'] == voter_uid
    assert new_vote_data['targetId'] == target_uid
    assert new_vote_data['round'] == 2

@pytest.mark.parametrize("game_data, voter_uid, target_uid, expected_error", [
    ({"status": "waiting", "roundPhase": "VOTING", "players": [{"uid": "p1"}, {"uid": "p2"}]}, "p1", "p2", "This game is not currently in progress."),
    ({"status": "in_progress", "roundPhase": "ANSWER_SUBMISSION", "players": [{"uid": "p1"}, {"uid": "p2"}]}, "p1", "p2", "It is not currently time to vote."),
    ({"status": "in_progress", "roundPhase": "VOTING", "players": [{"uid": "p1"}, {"uid": "p2"}]}, "p1", "p1", "You cannot vote for yourself."),
    ({"status": "in_progress", "roundPhase": "VOTING", "players": [{"uid": "p2"}]}, "p1", "p2", "You are not a player in this game."),
    ({"status": "in_progress", "roundPhase": "VOTING", "players": [{"uid": "p1"}]}, "p1", "p2", "The targeted player is not in this game."),
    ({"status": "in_progress", "roundPhase": "VOTING", "players": [{"uid": "p1"}, {"uid": "p2"}], "votes": [{"voterId": "p1", "round": 1}], "currentRound": 1}, "p1", "p2", "You have already voted in this round."),
])
def test_submit_vote_failures(mock_firestore_client, game_data, voter_uid, target_uid, expected_error):
    # Arrange
    mock_game_doc = MagicMock()
    mock_game_doc.exists = True
    mock_game_doc.to_dict.return_value = game_data
    mock_firestore_client.collection.return_value.document.return_value.get.return_value = mock_game_doc
    
    # Act & Assert
    with pytest.raises(ValueError, match=expected_error):
        game_service.submit_vote("any_game", voter_uid, target_uid)

def test_tally_votes_eliminates_player_and_advances_round(mock_firestore_client, mocker):
    """
    Tests that a player with the most votes is correctly eliminated and the game
    advances to the next round.
    """
    # Arrange
    now = datetime.now(timezone.utc)
    mocker.patch('app.services.game_service.datetime.datetime', mocker.Mock(now=lambda tz: now))
    
    game_data = {
        "status": "in_progress", "roundPhase": "VOTING", "currentRound": 2,
        "roundEndTime": now - timedelta(seconds=1),
        "players": [
            {"uid": "p1", "isImpostor": False},
            {"uid": "p2", "isImpostor": True},
            {"uid": "p3", "isImpostor": False},
        ],
        "votes": [
            {"voterId": "p1", "targetId": "p2", "round": 2},
            {"voterId": "p3", "targetId": "p2", "round": 2},
        ]
    }
    mock_game_doc = MagicMock()
    mock_game_doc.exists = True
    mock_game_doc.to_dict.return_value = game_data
    
    mock_transaction = mock_firestore_client.transaction.return_value
    game_ref = mock_firestore_client.collection.return_value.document.return_value
    game_ref.get.return_value = mock_game_doc

    # Act
    game_service.tally_votes("any_game")

    # Assert
    update_call_args = mock_transaction.update.call_args[0][1]
    
    # After eliminating the only impostor, the game should end.
    assert update_call_args["status"] == "finished"
    assert update_call_args["roundPhase"] == "GAME_ENDED"
    assert update_call_args["winner"] == "humans"
    
    eliminated_player = next(p for p in update_call_args["players"] if p["uid"] == "p2")
    assert eliminated_player.get("isEliminated") is True

@pytest.mark.parametrize("game_data, expected_winner", [
    # Human victory: last impostor is eliminated
    ({"players": [{"uid": "p1", "isImpostor": False}, {"uid": "p2", "isImpostor": True, "isEliminated": True}]}, "humans"),
    # AI victory: impostors equal humans
    ({"players": [{"uid": "p1", "isImpostor": False}, {"uid": "p2", "isImpostor": True}]}, "ai"),
    # AI victory: round 3 ends
    ({"currentRound": 3, "players": [{"uid": "p1", "isImpostor": False}, {"uid": "p2", "isImpostor": True}]}, "ai"),
])
def test_tally_votes_win_conditions(mock_firestore_client, mocker, game_data, expected_winner):
    # Arrange
    now = datetime.now(timezone.utc)
    mocker.patch('app.services.game_service.datetime.datetime', mocker.Mock(now=lambda tz: now))
    
    full_game_data = {
        "status": "in_progress", "roundPhase": "VOTING",
        "roundEndTime": now - timedelta(seconds=1),
        "votes": [],
        "currentRound": game_data.get("currentRound", 2),
        "players": game_data.get("players")
    }
    mock_game_doc = MagicMock()
    mock_game_doc.exists = True
    mock_game_doc.to_dict.return_value = full_game_data
    
    mock_transaction = mock_firestore_client.transaction.return_value
    game_ref = mock_firestore_client.collection.return_value.document.return_value
    game_ref.get.return_value = mock_game_doc
    
    # Act
    game_service.tally_votes("any_game")
    
    # Assert
    update_call_args = mock_transaction.update.call_args[0][1]
    assert update_call_args["status"] == "finished"
    assert update_call_args["roundPhase"] == "GAME_ENDED"
    assert update_call_args["winner"] == expected_winner
