# Schema Model Improvements - Recommendations

## Fields That Should Be Changed to Literal Types

Based on analysis of `backend/app/services/game_service.py`, the following fields currently use free-form strings but only have 2-3 actual values in practice:

---

### 1. `GameResultLastRound.reason` - **HIGH PRIORITY**

**Current Definition:**
```python
class GameResultLastRound(BaseModel):
    reason: str = Field(..., description="Why the game ended")
```

**Actual Values Used (from game_service.py):**
- Line 753: `"All impostors have been eliminated. Humans win!"`
- Line 762: `"Maximum rounds reached with surviving impostors. AI win."`
- Line 648 (fallback): `"game_ended"` (default if missing)

**Problem:** These are verbose user-facing messages, not enum codes.

**Recommendation:** Split into two fields:

```python
class GameResultLastRound(BaseModel):
    eliminatedPlayer: Optional[str] = Field(None, description="UID of player eliminated in final round")

    # NEW: Enum code for analytics queries
    endCondition: Literal[
        "all_impostors_eliminated",  # Humans win - all AI caught
        "max_rounds_reached",         # AI win - survived to end
        "vote_tie_no_elimination"     # Edge case - tie vote at end
    ] = Field(..., description="How the game ended (enum for queries)")

    # Keep verbose message for UI display
    endReasonMessage: str = Field(..., description="User-facing explanation of game end")

    voteCounts: dict[str, int] = Field(default_factory=dict, description="Final vote tallies (playerId -> count)")
```

**Benefits:**
- ✅ Analytics queries can use `WHERE endCondition = 'all_impostors_eliminated'`
- ✅ Type safety - can't accidentally use wrong string
- ✅ UI still gets friendly messages

---

### 2. `GameResultPlayer.eliminatedInRound` - **MEDIUM PRIORITY**

**Current Definition:**
```python
class GameResultPlayer(BaseModel):
    eliminatedInRound: Optional[int] = Field(None, description="Round number when eliminated (if applicable)")
```

**Issue:** Currently hardcoded to `None` in archive function (line 578):
```python
eliminatedInRound=None  # TODO: Track elimination rounds in future
```

**Recommendation:** Either:
- **Option A:** Remove field entirely until tracking is implemented
- **Option B:** Keep field but update `tally_votes()` to set `eliminatedInRound` when player is eliminated

**If keeping, validate round numbers:**
```python
eliminatedInRound: Optional[Literal[1, 2, 3]] = Field(
    None,
    description="Round number when eliminated (None if survived)"
)
```

---

### 3. Add Missing Enum: `eliminatedRole` - **LOW PRIORITY**

**Currently Missing from GameResultLastRound but used in game_service.py:**

Line 789-791:
```python
"eliminatedRole": eliminated_role,  # "AI" or "Human" or "Tie"
```

But `GameResultLastRound` doesn't have this field! It should:

```python
class GameResultLastRound(BaseModel):
    eliminatedPlayer: Optional[str] = Field(None, description="UID of eliminated player")
    eliminatedRole: Optional[Literal["AI", "Human", "Tie"]] = Field(
        None,
        description="Role of eliminated player for analytics"
    )
    # ... other fields
```

---

## Summary of Changes Needed

### game.py Changes:

```python
# Current GameResultLastRound
class GameResultLastRound(BaseModel):
    eliminatedPlayer: Optional[str] = Field(None, description="UID of player eliminated in final round")
    reason: str = Field(..., description="Why the game ended")  # ❌ TOO LOOSE
    voteCounts: dict[str, int] = Field(default_factory=dict, description="Vote tallies for final round")

# Improved GameResultLastRound
class GameResultLastRound(BaseModel):
    eliminatedPlayer: Optional[str] = Field(None, description="UID of player eliminated in final round")
    eliminatedRole: Optional[Literal["AI", "Human", "Tie"]] = Field(
        None,
        description="Role of eliminated player"
    )

    # Split reason into enum + message
    endCondition: Literal[
        "all_impostors_eliminated",
        "max_rounds_reached"
    ] = Field(..., description="Game end condition (for queries)")

    endReasonMessage: str = Field(..., description="User-facing explanation")

    voteCounts: dict[str, int] = Field(
        default_factory=dict,
        description="Final round vote tallies (playerId -> vote count)"
    )
```

### game_service.py Changes:

Update the `tally_votes()` function where `round_result` is constructed (line 785-797):

```python
# Determine end condition enum
end_condition = None
if len(active_impostors) == 0:
    end_condition = "all_impostors_eliminated"
elif current_round >= 3:
    end_condition = "max_rounds_reached"

round_result = {
    "round": current_round,
    "totalVotes": len(votes_this_round),
    "votes": votes_summary,
    "eliminatedPlayerId": eliminated_player.get("uid") if eliminated_player else None,
    "eliminatedPlayerName": eliminated_player.get("gameDisplayName") if eliminated_player else None,
    "eliminatedRole": eliminated_role,  # Already exists
    "summary": summary_text,
    "gameEnded": game_is_over,
    "endCondition": end_condition,  # NEW
    "endReasonMessage": end_reason  # RENAMED from endReason
}
```

Update archive function (line 646-650):

```python
last_round_result = GameResultLastRound(
    eliminatedPlayer=last_round_result_data.get("eliminatedPlayerId"),
    eliminatedRole=last_round_result_data.get("eliminatedRole"),  # NEW
    endCondition=last_round_result_data.get("endCondition", "max_rounds_reached"),  # NEW
    endReasonMessage=last_round_result_data.get("endReasonMessage", "Game ended"),  # RENAMED
    voteCounts=last_round_result_data.get("voteCounts", {})
)
```

---

## Benefits of These Changes

1. **Better Analytics Queries:**
   ```sql
   SELECT aiModelUsed, COUNT(*)
   FROM game_analytics
   WHERE lastRoundResult.endCondition = 'all_impostors_eliminated'
   GROUP BY aiModelUsed
   ```

2. **Type Safety:**
   - Pydantic will reject invalid enum values at write time
   - No typos like "all_imposters_eliminated" vs "all_impostors_eliminated"

3. **Self-Documenting:**
   - Enum values clearly show all possible outcomes
   - No need to scan code to find what strings are used

4. **Future-Proof:**
   - Easy to add new end conditions (e.g., "humans_eliminated", "timeout")
   - BigQuery schema can use ENUM type

---

## Implementation Priority

1. **HIGH:** Fix `reason` → `endCondition` + `endReasonMessage`
2. **MEDIUM:** Add missing `eliminatedRole` field
3. **LOW:** Decide on `eliminatedInRound` (remove or implement tracking)

---

**Status:** Recommendations ready for review. Awaiting approval to implement changes.
