from fastapi import APIRouter, Depends, HTTPException, status
from app.models.game import (
    CreateGameRequest,
    CreateGameResponse,
    PublicGame,
    SubmitAnswerRequest,
    VoteRequest
)
from app.api.deps import get_current_user
from app.services import game_service
from typing import List
import logging

logger = logging.getLogger(__name__)

# APIRouter creates a "mini" application that can be included in the main app.
# This helps organize the code.
router = APIRouter()

@router.get(
    "/",
    response_model=List[PublicGame],
    summary="List public games"
)
def list_public_games_endpoint():
    """
    Retrieves a list of all public game rooms that are currently waiting for players.
    """
    try:
        games = game_service.list_public_games()
        return games
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )


@router.post(
    "/{game_id}/join",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Join a game"
)
def join_game_endpoint(game_id: str, user_uid: str = Depends(get_current_user)):
    """
    Allows an authenticated user to join an existing game.
    """
    try:
        game_service.join_game(game_id, user_uid)
        return
    except ValueError as e:
        # These are expected errors (game full, etc.)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )

@router.post(
    "/{game_id}/vote",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Vote for a player"
)
def vote_endpoint(
    game_id: str,
    request: VoteRequest,
    user_uid: str = Depends(get_current_user)
):
    """
    Allows an authenticated player to cast a vote for who they believe
    is the impostor in the current round.

    The vote submission uses Firestore transactions to handle concurrent votes
    safely and ensure exactly one request triggers vote tallying.
    """
    try:
        game_service.submit_vote(
            game_id=game_id,
            voter_uid=user_uid,
            target_uid=request.votedForId
        )
        return
    except ValueError as e:
        # Expected errors (validation failures, transaction conflicts)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected errors - log for debugging
        logger.exception(f"Unexpected error in vote endpoint for game {game_id}, user {user_uid}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your vote."
        )

@router.post(
    "/{game_id}/submit-answer",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Submit an answer for the current round"
)
def submit_answer_endpoint(
    game_id: str,
    request: SubmitAnswerRequest,
    user_uid: str = Depends(get_current_user)
):
    """
    Submits a player's answer for the current round.
    The answer is stored temporarily and is not revealed until the round ends.
    """
    try:
        game_service.submit_answer(game_id, user_uid, request.answer)
        return
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )

@router.post(
    "/{game_id}/tally-answers",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Tally answers and transition to voting phase"
)
def tally_answers_endpoint(game_id: str, user_uid: str = Depends(get_current_user)):
    """
    Triggered by a client when the answer submission timer expires.
    The backend validates the time and transitions the game to the VOTING phase.
    """
    try:
        game_service.tally_answers(game_id)
        return
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )

@router.post(
    "/{game_id}/tally-votes",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Tally votes and end the round"
)
def tally_votes_endpoint(game_id: str, user_uid: str = Depends(get_current_user)):
    """
    Triggered by a client when the voting timer expires.
    The backend validates the time, tallies votes, handles eliminations,
    and transitions the game to the next round or ends it.
    """
    try:
        game_service.tally_votes(game_id)
        return
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )

@router.post(
    "/{game_id}/start",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Start a game"
)
def start_game_endpoint(game_id: str, user_uid: str = Depends(get_current_user)):
    """
    Allows the host to start the game. This will lock the room and assign impostors.
    """
    try:
        game_service.start_game(game_id, user_uid)
        return
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )

@router.post(
    "/",
    response_model=CreateGameResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new game room"
)
def create_game_endpoint(
    request_body: CreateGameRequest,
    host_uid: str = Depends(get_current_user)
):
    """
    Creates a new game room. The user who makes this request is the host.
    """
    try:
        # The request_body (a CreateGameRequest object) is already validated by FastAPI.
        # The host_uid is validated by our authentication dependency.

        # Pass the Pydantic model directly to the service layer.
        game_id = game_service.create_game(host_uid=host_uid, settings=request_body)

        # Return the ID of the new game along with the selected model.
        return CreateGameResponse(gameId=game_id, aiModelId=request_body.aiModelId)
    except Exception as e:
        # A generic error handler for any unexpected issues.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )
