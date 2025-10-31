from firebase_admin import firestore
from app.services.firebase_service import get_firestore_client
from app.models.game import CreateGameRequest
from app.services import model_catalog
from app.services import ai_service
from app.utils import helpers
import datetime
import random
import uuid
import logging
from collections import Counter
from google.api_core.exceptions import FailedPrecondition, Aborted

logger = logging.getLogger(__name__)


QUESTION_BANK = {
    "en": [
        "What is your favorite weekend activity?",
        "Describe your ideal vacation destination.",
        "What was the last book you enjoyed reading?",
        "If you could learn any new skill instantly, what would it be?",
        "What is a food you never get tired of?",
        "What's your go-to comfort food after a long day?",
        "Are you an early bird or a night owl, and why?",
        "Which song have you been replaying lately?",
        "What's a hobby you do to unwind after work or school?",
        "Coffee or tea—how do you like it?",
        "What's one small thing that always improves your day?",
        "What's your favorite way to spend a rainy afternoon?",
    ],
    "ko": [
        "주말에 가장 좋아하는 활동은 무엇인가요?",
        "이상적인 휴가지에 대해 설명해 주세요.",
        "최근에 재미있게 읽은 책은 무엇인가요?",
        "새로운 기술을 바로 배울 수 있다면 무엇을 배우고 싶나요?",
        "질리지 않고 계속 먹을 수 있는 음식은 무엇인가요?",
        "긴 하루 끝에 찾게 되는 소울푸드는 무엇인가요?",
        "아침형인가요, 저녁형인가요? 그 이유는?",
        "요즘 자주 반복해서 듣는 노래는 무엇인가요?",
        "퇴근/하교 후 마음을 풀기 위해 하는 취미가 있나요?",
        "커피와 차 중 무엇을 더 선호하고, 어떻게 마시는 편인가요?",
        "하루를 조금 더 좋게 만드는 작은 습관은 무엇인가요?",
        "비 오는 오후를 가장 좋아하는 보내는 방법은 무엇인가요?",
    ],
}

AI_PLACEHOLDER_TEMPLATE = "This is a template message for testing round {round}."


def _select_round_question(language: str) -> str:
    pool = QUESTION_BANK.get(language, QUESTION_BANK["en"])
    return random.choice(pool)


def _extract_round_histories(game_ref, current_round: int):
    """Extract public answers from completed rounds for prompt context.

    Builds a per-round history that captures every player's revealed answer.

    Args:
        game_ref: Firestore document reference to the game.
        current_round: The round we are about to generate answers for.

    Returns:
        List of dicts ordered by round number. Each dict has:
            - round: int
            - question: str
            - answers: List[{"player": str, "role": str, "text": str}]
    """
    if current_round <= 1:
        return []

    try:
        game_doc = game_ref.get()
        game_data = game_doc.to_dict() if game_doc else None
        if not game_data:
            logger.warning(
                "Could not fetch game data for round history extraction. "
                "Game: %s", game_ref.id
            )
            return []

        rounds_data = game_data.get("rounds", [])
        players_index = {p.get("uid"): p for p in game_data.get("players", [])}

        db = get_firestore_client()
        pending_ref = game_ref.collection("pending_messages")
        messages_ref = game_ref.collection("messages")

        pending_query = (pending_ref
                         .where("roundNumber", "<", current_round))
        messages_query = (messages_ref
                          .where("roundNumber", "<", current_round)
                          .order_by("roundNumber"))

        round_map = {}
        pending_messages = list(pending_query.stream())
        stored_messages = list(messages_query.stream())
        all_messages = pending_messages + stored_messages

        # Sort deterministically by round number then timestamp (if present)
        def sort_key(msg_doc):
            msg_data = msg_doc.to_dict()
            round_num = msg_data.get("roundNumber") or 0
            timestamp = msg_data.get("timestamp")
            return (
                round_num,
                timestamp if timestamp is not None else 0
            )

        all_messages.sort(key=sort_key)

        for msg_doc in all_messages:
            msg_data = msg_doc.to_dict()
            round_num = msg_data.get("roundNumber")
            if not round_num:
                logger.warning(
                    "Message %s missing roundNumber field. Game: %s",
                    msg_doc.id,
                    game_ref.id
                )
                continue

            entry = round_map.setdefault(round_num, {
                "round": round_num,
                "question": rounds_data[round_num - 1].get("question", "")
                if round_num - 1 < len(rounds_data) else "",
                "answers": []
            })

            sender_id = msg_data.get("senderId") or msg_data.get("authorId")
            player = players_index.get(sender_id) if sender_id else None
            role = "ai" if player and player.get("isImpostor") else "human"

            entry["answers"].append({
                "player": (player.get("gameDisplayName") if player else msg_data.get("senderName") or "Unknown"),
                "role": role,
                "text": msg_data.get("text") or msg_data.get("content") or ""
            })

        histories = [round_map[r] for r in sorted(round_map.keys())]

        expected_rounds = set(range(1, current_round))
        missing_rounds = expected_rounds - set(round_map.keys())
        if missing_rounds:
            logger.warning(
                "Missing messages for rounds %s when building history. Game: %s",
                sorted(missing_rounds),
                game_ref.id
            )

        return histories

    except Exception as exc:
        logger.exception(
            "Error extracting round histories. Game: %s, Round: %s. Error: %s",
            game_ref.id,
            current_round,
            exc
        )
        return []


def _enqueue_ai_answers(game_ref, ai_players, round_number):
    """Generate and enqueue AI answers for the current round.

    Uses ai_service to generate actual AI responses for each AI player.

    Args:
        game_ref: Firestore document reference to the game
        ai_players: List of AI player dictionaries
        round_number: Current round number
    """
    db = get_firestore_client()
    pending_ref = game_ref.collection("pending_messages")
    batch = db.batch()

    # Get game data for context
    game_data = game_ref.get().to_dict()
    if not game_data:
        logger.error(f"Could not fetch game data for AI generation: {game_ref.id}")
        return

    # Get current round's question
    rounds = game_data.get("rounds", [])
    if round_number - 1 < len(rounds):
        current_question = rounds[round_number - 1].get("question", "")
    else:
        logger.error(
            f"Round {round_number} not found in game data: {game_ref.id}"
        )
        return

    for ai in ai_players:
        # Extract conversation history
        history = _extract_round_histories(
            game_ref,
            round_number
        )

        # Generate actual AI response
        try:
            ai_response = ai_service.generate_ai_response(
                model_id=game_data.get("aiModelId", "gpt-5"),
                question=current_question,
                language=game_data.get("language", "en"),
                round_number=round_number,
                conversation_history=history,
                game_id=game_ref.id
            )

            logger.info(
                f"Generated AI response for {ai.get('gameDisplayName')}: "
                f"game={game_ref.id}, round={round_number}, "
                f"length={len(ai_response)} chars"
            )

        except Exception as e:
            # If AI generation fails completely, use fallback
            logger.error(
                f"AI generation failed for {ai.get('gameDisplayName')}: "
                f"game={game_ref.id}, error={e}. Using fallback."
            )
            ai_response = AI_PLACEHOLDER_TEMPLATE.format(round=round_number)

        doc_ref = pending_ref.document()
        batch.set(doc_ref, {
            "authorId": ai.get("uid"),
            "senderId": ai.get("uid"),
            "senderName": ai.get("gameDisplayName"),
            "content": ai_response,
            "roundNumber": round_number,
            "submittedAt": firestore.SERVER_TIMESTAMP,
        })

    batch.commit()
    logger.info(
        f"Enqueued {len(ai_players)} AI responses for "
        f"game {game_ref.id}, round {round_number}"
    )

def create_game(host_uid: str, settings: CreateGameRequest) -> str:
    """
    Creates a new game room in Firestore.

    Args:
        host_uid: The UID of the user creating the game.
        settings: A Pydantic model containing the game settings.

    Returns:
        The ID of the newly created game document.
    """
    db = get_firestore_client()

    # Validate that the requested AI model is in our catalog.
    supported_models = {model["id"] for model in model_catalog.list_models()}
    if settings.aiModelId not in supported_models:
        raise ValueError("Requested AI model is not supported.")

    # Define the initial structure of the game document using the Pydantic model
    new_game_data = {
        "hostId": host_uid,
        "status": "waiting",
        "language": settings.language,
        "aiCount": settings.aiCount,
        "privacy": settings.privacy,
        "aiModelId": settings.aiModelId,
        "createdAt": firestore.SERVER_TIMESTAMP,

        # TTL: Auto-delete unstarted games after 15 minutes
        "ttl": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15),

        "currentRound": 0,
        "rounds": [],
        "players": [
            {
                "uid": host_uid,
                # "gameDisplayName" is removed. It will be assigned at game start.
                "isImpostor": False # Host is always human
            }
        ],
        "readyPlayerIds": [],
        "votes": [],
        "impostorInfo": {
            "aiModelId": settings.aiModelId
        }
    }

    # Add the new document to the 'game_rooms' collection
    # The ID is automatically generated by Firestore.
    _, game_ref = db.collection("game_rooms").add(new_game_data)
    
    return game_ref.id

def list_public_games():
    """
    Retrieves a list of public games that are waiting for players.

    Returns:
        A list of dictionaries, where each dictionary represents a public game.
    """
    db = get_firestore_client()
    
    games_ref = db.collection("game_rooms")
    
    # Create a query to find public games in the "waiting" state.
    query = games_ref.where("privacy", "==", "public").where("status", "==", "waiting")
    
    public_games = []
    for game in query.stream():
        game_data = game.to_dict()
        public_games.append({
            "gameId": game.id,
            "language": game_data.get("language"),
            "playerCount": len(game_data.get("players", [])),
            "maxPlayers": 4, # As per our game rules
            "aiModelId": game_data.get("aiModelId", "unknown")
        })
        
    return public_games

def join_game(game_id: str, user_uid: str):
    """
    Adds a player to a game room in Firestore.

    Args:
        game_id: The ID of the game to join.
        user_uid: The UID of the user joining the game.

    Raises:
        ValueError: If the game is full, not found, not waiting for players,
                    or if the player has already joined.
    """
    db = get_firestore_client()
    game_ref = db.collection("game_rooms").document(game_id)
    game_doc = game_ref.get()

    if not game_doc.exists:
        raise ValueError("Game not found.")

    game_data = game_doc.to_dict()
    players = game_data.get("players", [])

    if game_data.get("status") != "waiting":
        raise ValueError("This game is not waiting for players.")

    if len(players) >= 4:
        raise ValueError("This game is full.")

    if any(p["uid"] == user_uid for p in players):
        raise ValueError("You have already joined this game.")

    # In a real implementation, this would come from a helper function.
    new_player_name = "Witty Walrus" # Placeholder

    new_player = {
        "uid": user_uid,
        # "gameDisplayName" is removed. It will be assigned at game start.
        "isImpostor": False # Impostor status is assigned when the game starts
    }

    # Atomically add the new player to the 'players' array.
    game_ref.update({
        "players": firestore.ArrayUnion([new_player])
    })

def start_game(game_id: str, user_uid: str):
    """
    Starts the game, assigns impostors, and updates the game state.

    Args:
        game_id: The ID of the game to start.
        user_uid: The UID of the user attempting to start the game.

    Raises:
        ValueError: If the user is not the host, if there are not enough players,
                    or if the game is not in a 'waiting' state.
    """
    db = get_firestore_client()
    game_ref = db.collection("game_rooms").document(game_id)
    game_doc = game_ref.get()

    if not game_doc.exists:
        raise ValueError("Game not found.")

    game_data = game_doc.to_dict()

    if game_data.get("hostId") != user_uid:
        raise ValueError("Only the host can start the game.")

    if game_data.get("status") != "waiting":
        raise ValueError("The game has already started or is finished.")

    players = game_data.get("players", [])
    # For now, we will not require a minimum number of players to start the game.
    # if len(players) < 2:
        # raise ValueError("Not enough players to start the game (minimum 2).")

    ai_count = game_data.get("aiCount", 0)

    # Ensure all human players are marked as not impostors.
    for player in players:
        player['isImpostor'] = False

    # Create AI player objects and mark them as impostors.
    ai_players = []
    for _ in range(ai_count):
        ai_players.append({
            "uid": f"ai_{uuid.uuid4()}",
            # "gameDisplayName" will be assigned below.
            "isImpostor": True
        })

    # Combine human and AI players into a single list of all participants.
    all_participants = players + ai_players

    # NEW: Assign unique, random names to all participants at the same time.
    nicknames = helpers.generate_unique_nicknames(len(all_participants))
    for i, participant in enumerate(all_participants):
        participant["gameDisplayName"] = nicknames[i]

    # Shuffle the list to randomize player order for the frontend.
    random.shuffle(all_participants)
    
    # Set timers for the first round
    now = datetime.datetime.now(datetime.timezone.utc)
    # Using a short duration for easier testing; this would be longer in production.
    answer_duration = datetime.timedelta(seconds=90) 
    end_time = now + answer_duration

    question = _select_round_question(game_data.get("language", "en"))

    game_ref.update({
        "players": all_participants,
        "status": "in_progress",
        "roundPhase": "ANSWER_SUBMISSION", # Add the new granular state
        "currentRound": 1, # Start the first round
        "roundStartTime": now,
        "roundEndTime": end_time,

        # TTL: Extend expiration to 30 minutes from start time
        "ttl": now + datetime.timedelta(minutes=30),

        "impostorInfo": {
            **game_data.get("impostorInfo", {}),
            "aiModelId": game_data.get("aiModelId")
        },
        "rounds": [
            {
                "round": 1,
                "question": question,
            }
        ]
    })

    if ai_players:
        _enqueue_ai_answers(game_ref, ai_players, 1)

def tally_answers(game_id: str):
    """
    Transitions the game from ANSWER_SUBMISSION to VOTING.
    This is triggered by a client after the round timer expires. The function
    validates the time, moves pending messages to the main messages collection,
    and sets up the timer for the next phase.
    """
    db = get_firestore_client()
    game_ref = db.collection("game_rooms").document(game_id)

    game_doc = game_ref.get()
    if not game_doc.exists:
        raise ValueError("Game not found.")

    game_data = game_doc.to_dict()

    if game_data.get("status") != "in_progress":
        raise ValueError("This game is not currently in progress.")

    if game_data.get("roundPhase") != "ANSWER_SUBMISSION":
        return

    round_end_time = game_data.get("roundEndTime")
    if round_end_time and datetime.datetime.now(datetime.timezone.utc) < round_end_time.replace(tzinfo=datetime.timezone.utc):
        raise ValueError("Answer submission time has not ended yet.")

    pending_messages_ref = game_ref.collection("pending_messages")
    pending_messages = list(pending_messages_ref.stream())

    if pending_messages:
        batch = db.batch()
        messages_ref = game_ref.collection("messages")
        for msg in pending_messages:
            msg_data = msg.to_dict()
            normalized = {
                "text": msg_data.get("content"),
                "senderId": msg_data.get("senderId") or msg_data.get("authorId"),
                "senderName": msg_data.get("senderName"),
                "roundNumber": msg_data.get("roundNumber", game_data.get("currentRound", 0)),
                "timestamp": msg_data.get("submittedAt", firestore.SERVER_TIMESTAMP),
            }
            messages_doc = messages_ref.document(msg.id)
            batch.set(messages_doc, normalized)
            batch.delete(msg.reference)
        batch.commit()

    now = datetime.datetime.now(datetime.timezone.utc)
    current_round = game_data.get("currentRound", 0)

    if current_round == 1:
        answer_duration = datetime.timedelta(seconds=90)
        next_round_end_time = now + answer_duration
        next_round = current_round + 1
        question = _select_round_question(game_data.get("language", "en"))

        game_ref.update({
            "roundPhase": "ANSWER_SUBMISSION",
            "currentRound": next_round,
            "roundStartTime": now,
            "roundEndTime": next_round_end_time,
            "rounds": firestore.ArrayUnion([
                {"round": next_round, "question": question}
            ])
        })

        ai_players = [p for p in game_data.get("players", []) if p.get("isImpostor")]
        if ai_players:
            _enqueue_ai_answers(game_ref, ai_players, next_round)
    else:
        game_ref.update({
            "roundPhase": "VOTING",
            "roundStartTime": now,
            "roundEndTime": None
        })


def _archive_game_result(game_ref, game_data: dict, winner: str):
    """
    Archives a finished game to the game_results collection for analytics pipeline.

    This function extracts all relevant game data and writes it to Firestore's
    game_results collection, which serves as the staging layer before BigQuery archival.

    Args:
        game_ref: Firestore document reference to the finished game
        game_data: Dictionary containing the game's data snapshot
        winner: The game winner ("humans" or "ai")

    Note:
        This function is fault-tolerant - exceptions are logged but not re-raised
        to ensure gameplay completion is not affected by analytics failures.
    """
    from app.models.game import (
        GameResult, GameResultPlayer, GameResultRound,
        GameResultAnswer, GameResultVote, GameResultLastRound
    )

    db = get_firestore_client()
    game_id = game_ref.id

    try:
        logger.info(f"Starting game result archival for game {game_id}")

        # Extract basic game metadata
        language = game_data.get("language", "en")
        ai_model_used = game_data.get("aiModelId", "unknown")
        total_rounds = game_data.get("currentRound", 0)

        # Build players list
        players_data = game_data.get("players", [])
        players_list = []
        for player in players_data:
            players_list.append(GameResultPlayer(
                uid=player.get("uid"),
                gameDisplayName=player.get("gameDisplayName", "Unknown"),
                isImpostor=player.get("isImpostor", False),
                isEliminated=player.get("isEliminated", False),
                eliminatedInRound=None  # TODO: Track elimination rounds in future
            ))

        # Create player lookup for determining isAI flag
        player_lookup = {p.get("uid"): p for p in players_data}

        # Extract messages from subcollection and build rounds with answers
        messages_ref = game_ref.collection("messages")
        messages_docs = list(messages_ref.stream())

        # Group messages by round number
        rounds_map = {}
        rounds_metadata = game_data.get("rounds", [])

        for msg_doc in messages_docs:
            msg_data = msg_doc.to_dict()
            round_num = msg_data.get("roundNumber", 0)

            if round_num not in rounds_map:
                # Get question for this round from rounds metadata
                question = ""
                for round_meta in rounds_metadata:
                    if round_meta.get("round") == round_num:
                        question = round_meta.get("question", "")
                        break

                rounds_map[round_num] = {
                    "question": question,
                    "answers": []
                }

            # Determine if this answer is from AI
            sender_id = msg_data.get("senderId")
            player = player_lookup.get(sender_id)
            is_ai = player.get("isImpostor", False) if player else False

            rounds_map[round_num]["answers"].append(GameResultAnswer(
                playerId=sender_id or "unknown",
                playerName=msg_data.get("senderName", "Unknown"),
                text=msg_data.get("text", ""),
                isAI=is_ai
            ))

        # Build rounds list in order
        rounds_list = []
        for round_num in sorted(rounds_map.keys()):
            round_data = rounds_map[round_num]
            rounds_list.append(GameResultRound(
                roundNumber=round_num,
                question=round_data["question"],
                revealedAnswers=round_data["answers"]
            ))

        # Extract votes (add timestamp since votes don't currently have them)
        votes_data = game_data.get("votes", [])
        votes_list = []
        now = datetime.datetime.now(datetime.timezone.utc)

        for vote in votes_data:
            votes_list.append(GameResultVote(
                roundNumber=vote.get("round", 0),
                voterId=vote.get("voterId", "unknown"),
                targetId=vote.get("targetId", "unknown"),
                timestamp=now  # Backfilled timestamp for MVP
            ))

        # Extract last round result (analytics data only, UI messages excluded)
        last_round_result_data = game_data.get("lastRoundResult", {})
        last_round_result = GameResultLastRound(
            eliminatedPlayer=last_round_result_data.get("eliminatedPlayerId"),
            eliminatedRole=last_round_result_data.get("eliminatedRole"),
            endCondition=last_round_result_data.get("endCondition", "max_rounds_reached"),
            voteCounts=last_round_result_data.get("voteCounts", {})
            # Note: endReasonMessage intentionally excluded - UI derives messages from endCondition
        )

        # Build complete GameResult object
        game_result = GameResult(
            gameId=game_id,
            endedAt=datetime.datetime.now(datetime.timezone.utc),
            language=language,
            aiModelUsed=ai_model_used,
            winner=winner,
            totalRounds=total_rounds,
            players=players_list,
            rounds=rounds_list,
            votes=votes_list,
            lastRoundResult=last_round_result
        )

        # Convert to dict for Firestore (Pydantic model_dump handles datetime serialization)
        game_result_dict = game_result.model_dump(mode='json')

        # Write to game_results collection
        db.collection("game_results").add(game_result_dict)

        logger.info(f"✓ Successfully archived game {game_id} to game_results collection")

    except Exception as e:
        # Log error but don't re-raise - analytics failure should not affect gameplay
        logger.error(
            f"Failed to archive game {game_id} to game_results: {e}",
            exc_info=True
        )
        # TODO: Consider writing to a 'failed_archives' collection for manual recovery


def tally_votes(game_id: str):
    """Counts votes, applies eliminations, and advances to the next phase."""
    db = get_firestore_client()
    game_ref = db.collection("game_rooms").document(game_id)

    game_doc = game_ref.get()
    if not game_doc.exists:
        raise ValueError("Game not found.")

    game_data = game_doc.to_dict()

    if game_data.get("status") != "in_progress":
        raise ValueError("This game is not currently in progress.")

    if game_data.get("roundPhase") != "VOTING":
        return

    current_round = game_data.get("currentRound", 0)
    votes_this_round = [v for v in game_data.get("votes", []) if v.get("round") == current_round]

    vote_counts = Counter(v["targetId"] for v in votes_this_round)
    votes_summary = []
    for target_id, count in vote_counts.most_common():
        target_player = next((p for p in game_data["players"] if p["uid"] == target_id), None)
        votes_summary.append({
            "targetId": target_id,
            "targetName": target_player.get("gameDisplayName") if target_player else "Unknown",
            "voteCount": count,
            "isImpostor": target_player.get("isImpostor") if target_player else None,
        })

    eliminated_player = None
    eliminated_role = None
    if votes_this_round:
        most_votes = vote_counts.most_common(2)
        if len(most_votes) == 1 or (len(most_votes) > 1 and most_votes[0][1] > most_votes[1][1]):
            player_to_eliminate_uid = most_votes[0][0]
            for player in game_data["players"]:
                if player["uid"] == player_to_eliminate_uid:
                    player["isEliminated"] = True
                    eliminated_player = player
                    eliminated_role = "AI" if player.get("isImpostor") else "Human"
                    break

    active_players = [p for p in game_data["players"] if not p.get("isEliminated")]
    active_impostors = [p for p in active_players if p.get("isImpostor")]
    active_humans = [p for p in active_players if not p.get("isImpostor")]

    update_payload = {
        "players": game_data["players"],
    }

    if votes_this_round:
        summary_text = (
            f"{eliminated_player.get('gameDisplayName')} was eliminated ({eliminated_role})."
            if eliminated_player else "Votes tied. No one was eliminated."
        )
    else:
        summary_text = "No votes were cast this round."

    game_is_over = False
    end_condition = None
    end_reason_message = None
    if len(active_impostors) == 0:
        update_payload.update({
            "status": "finished",
            "roundPhase": "GAME_ENDED",
            "winner": "humans",
            "ttl": firestore.DELETE_FIELD  # Remove TTL - finished games never expire
        })
        game_is_over = True
        end_condition = "all_impostors_eliminated"
        end_reason_message = "All impostors have been eliminated. Humans win!"
    elif current_round >= 3:
        update_payload.update({
            "status": "finished",
            "roundPhase": "GAME_ENDED",
            "winner": "ai",
            "ttl": firestore.DELETE_FIELD  # Remove TTL - finished games never expire
        })
        game_is_over = True
        end_condition = "max_rounds_reached"
        end_reason_message = "Maximum rounds reached with surviving impostors. AI win."

    if not game_is_over:
        now = datetime.datetime.now(datetime.timezone.utc)
        answer_duration = datetime.timedelta(seconds=90)
        next_round_end_time = now + answer_duration
        next_round = current_round + 1
        question = _select_round_question(game_data.get("language", "en"))

        update_payload.update({
            "currentRound": next_round,
            "roundPhase": "ANSWER_SUBMISSION",
            "roundStartTime": now,
            "roundEndTime": next_round_end_time,
            "rounds": firestore.ArrayUnion([
                {"round": next_round, "question": question}
            ])
        })

        ai_players = [p for p in game_data.get("players", []) if p.get("isImpostor")]
        if ai_players:
            _enqueue_ai_answers(game_ref, ai_players, next_round)

    round_result = {
        "round": current_round,
        "totalVotes": len(votes_this_round),
        "votes": votes_summary,
        "voteCounts": dict(vote_counts),  # Vote tally for BigQuery analytics
        "eliminatedPlayerId": eliminated_player.get("uid") if eliminated_player else None,
        "eliminatedPlayerName": eliminated_player.get("gameDisplayName") if eliminated_player else None,
        "eliminatedRole": eliminated_role,
        "summary": summary_text,
        "gameEnded": game_is_over,
    }

    if game_is_over:
        round_result["endCondition"] = end_condition
        round_result["endReasonMessage"] = end_reason_message

    update_payload["lastRoundResult"] = round_result

    game_ref.update(update_payload)

    # Archive game results when game ends (round 2 or 3)
    if game_is_over:
        winner = update_payload.get("winner")
        _archive_game_result(game_ref, game_data, winner)

def submit_vote(game_id: str, voter_uid: str, target_uid: str):
    """
    Submits a player's vote for the current round using a Firestore transaction.

    This function uses transactions to prevent race conditions when multiple players
    vote simultaneously. The transaction ensures that exactly one request will trigger
    vote tallying when all votes are in.

    Args:
        game_id: The ID of the game.
        voter_uid: The UID of the player casting the vote.
        target_uid: The UID of the player being voted for.

    Raises:
        ValueError: If the game state is invalid for voting or the vote is invalid.
    """
    db = get_firestore_client()
    game_ref = db.collection("game_rooms").document(game_id)

    @firestore.transactional
    def _submit_vote_transaction(transaction):
        """
        Transactional function to read, validate, write vote, and determine if tallying needed.

        This function will be automatically retried by Firestore if a conflict is detected.
        It must be idempotent (safe to run multiple times).
        """
        # Read game state within the transaction
        game_doc = game_ref.get(transaction=transaction)

        if not game_doc.exists:
            raise ValueError("Game not found.")

        game_data = game_doc.to_dict()

        # Validate game state
        if game_data.get("status") != "in_progress":
            raise ValueError("This game is not currently in progress.")

        if game_data.get("roundPhase") != "VOTING":
            raise ValueError("It is not currently time to vote.")

        # Validate voter and target
        if voter_uid == target_uid:
            raise ValueError("You cannot vote for yourself.")

        players = game_data.get("players", [])
        player_uids = {p["uid"] for p in players}

        if voter_uid not in player_uids:
            raise ValueError("You are not a player in this game.")
        if target_uid not in player_uids:
            raise ValueError("The targeted player is not in this game.")

        # Check for duplicate votes
        current_round = game_data.get("currentRound", 0)
        votes = game_data.get("votes", [])

        if any(v["voterId"] == voter_uid and v.get("round") == current_round for v in votes):
            raise ValueError("You have already voted in this round.")

        # Create and write the new vote
        new_vote = {
            "voterId": voter_uid,
            "targetId": target_uid,
            "round": current_round
        }

        transaction.update(game_ref, {
            "votes": firestore.ArrayUnion([new_vote])
        })

        # Determine if tallying should occur
        # This uses the snapshot data from the transaction read
        total_required_votes = sum(1 for p in players if not p.get("isEliminated") and not p.get("isImpostor"))
        votes_this_round = [v for v in votes if v.get("round") == current_round]
        votes_this_round.append(new_vote)  # Include the vote we just added

        # Return True if all required votes are in
        return total_required_votes > 0 and len(votes_this_round) >= total_required_votes

    # Execute the transaction
    try:
        transaction = db.transaction()
        should_tally = _submit_vote_transaction(transaction)

        # If this was the final vote, trigger tallying (outside the transaction)
        if should_tally:
            logger.info(f"All votes received for game {game_id}. Triggering tally.")
            tally_votes(game_id)

    except (FailedPrecondition, Aborted) as e:
        # Transaction failed after maximum retries due to conflicts
        logger.error(f"Vote submission failed for game {game_id} due to transaction conflicts: {e}")
        raise ValueError("Unable to submit vote due to high activity. Please try again.")
    except ValueError:
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        # Unexpected error
        logger.exception(f"Unexpected error submitting vote for game {game_id}: {e}")
        raise ValueError("An unexpected error occurred while submitting your vote.")

def submit_answer(game_id: str, user_uid: str, answer: str):
    """
    Submits a player's answer for the current round.

    Args:
        game_id: The ID of the game.
        user_uid: The UID of the player submitting the answer.
        answer: The text of the answer.

    Raises:
        ValueError: If the game state is invalid for submission or the
                    player is not eligible to submit.
    """
    db = get_firestore_client()
    game_ref = db.collection("game_rooms").document(game_id)
    game_doc = game_ref.get()

    if not game_doc.exists:
        raise ValueError("Game not found.")

    game_data = game_doc.to_dict()
    
    if game_data.get("status") != "in_progress":
        raise ValueError("This game is not currently in progress.")
        
    if game_data.get("roundPhase") != "ANSWER_SUBMISSION":
        raise ValueError("It is not currently time to submit answers.")
        
    players = game_data.get("players", [])
    if not any(p["uid"] == user_uid for p in players):
        raise ValueError("You are not a player in this game.")
        
    # Store the answer in the pending_messages subcollection
    pending_messages_ref = game_ref.collection("pending_messages")

    current_round = game_data.get("currentRound", 0)
    existing_answer_query = pending_messages_ref.where("authorId", "==", user_uid).where("roundNumber", "==", current_round).limit(1).get()
    if existing_answer_query:
        raise ValueError("You have already submitted an answer for this round.")
        
    player_entry = next((p for p in players if p["uid"] == user_uid), None)
    if not player_entry:
        raise ValueError("Player not found in this game.")

    new_answer = {
        "authorId": user_uid,
        "senderId": user_uid,
        "senderName": player_entry.get("gameDisplayName"),
        "content": answer,
        "roundNumber": current_round,
        "submittedAt": firestore.SERVER_TIMESTAMP
    }
    
    pending_messages_ref.add(new_answer)
