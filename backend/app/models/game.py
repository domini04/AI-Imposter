from pydantic import BaseModel, Field
from typing import Literal


class CreateGameRequest(BaseModel):
    """Request body for creating a new game room."""
    language: Literal["en", "ko"] = Field(..., description="Language for this game room")
    aiCount: int = Field(..., ge=1, le=2, description="Number of AI impostors (1-2)")
    privacy: Literal["public", "private"] = Field(..., description="Visibility of the room")


class CreateGameResponse(BaseModel):
    """Response returned after successfully creating a game room."""
    gameId: str = Field(..., description="Unique identifier of the created game room")


class PublicGame(BaseModel):
    """A public game listing item returned by GET /games."""
    gameId: str = Field(..., description="Unique identifier of the game room")
    language: Literal["en", "ko"] = Field(..., description="Language of the game room")
    playerCount: int = Field(..., ge=0, description="Current number of players in the room")
    maxPlayers: int = Field(..., ge=1, description="Maximum number of players allowed")


class VoteRequest(BaseModel):
    """Request body for casting a vote in the voting phase."""
    votedForId: str = Field(..., description="UID of the player being voted for")


class KickPlayerRequest(BaseModel):
    """Request body for the host to kick a player from the room."""
    playerIdToKick: str = Field(..., description="UID of the player to remove")


class MessageResponse(BaseModel):
    """Generic message response for success/confirmation messages."""
    message: str = Field(..., description="Human-readable confirmation or status message")


class SubmitAnswerRequest(BaseModel):
    answer: str
