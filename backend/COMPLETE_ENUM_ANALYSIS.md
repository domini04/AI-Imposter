# Complete Enum Analysis for Game Result Fields

## Analysis Date: January 2025
## Based on: game_service.py (tally_votes function), gameplay_rules.md

---

## 1. ALL Possible Game End Conditions

### Currently Implemented in Code:

From `game_service.py:745-762`:

| Condition | Code Line | Logic | Winner | Label Suggestion |
|-----------|-----------|-------|--------|------------------|
| **All AI eliminated** | 745-753 | `len(active_impostors) == 0` | `"humans"` | `"all_impostors_eliminated"` |
| **Max rounds reached** | 754-762 | `current_round >= 3` (with surviving AI) | `"ai"` | `"max_rounds_reached"` |

### Edge Cases Not Currently Handled:

Based on gameplay_rules.md and logic analysis:

| Scenario | Currently Happens | Winner | Should Add? | Suggested Label |
|----------|-------------------|--------|-------------|-----------------|
| **All humans eliminated** | ❌ Not possible (AI can't vote) | N/A | ❌ No | N/A |
| **Tie vote at end (Round 3)** | ✅ Covered by "max_rounds_reached" | `"ai"` | ✅ Already handled | (same as max_rounds) |
| **No votes cast at all** | ✅ Summary text changes but game continues | N/A | ❌ No | N/A |
| **Game abandoned/timeout** | ❌ Not implemented (TTL handles cleanup) | N/A | 🤔 Future | `"game_abandoned"` |

---

## 2. Recommended Enum Definition

### Option A: Keep It Simple (Current Implementation Only)

```python
endCondition: Literal[
    "all_impostors_eliminated",  # Humans win - all AI caught
    "max_rounds_reached"          # AI win - survived to round 3 end
]
```

**Pros:** Matches current implementation exactly
**Cons:** No room for future edge cases

---

### Option B: Include Future-Proofing (RECOMMENDED)

```python
endCondition: Literal[
    "all_impostors_eliminated",  # Humans win - all AI caught before round 3 ends
    "max_rounds_reached",         # AI win - at least one AI survived to round 3 end
    "game_abandoned"              # Game ended due to inactivity/timeout (future use)
]
```

**Pros:** Allows for future timeout/abandon feature without schema migration
**Cons:** Currently unused value exists in schema

---

## 3. Eliminated Role Values

From `game_service.py:724`:

```python
eliminated_role = "AI" if player.get("isImpostor") else "Human"
```

But also from `game_service.py:738`:

```python
summary_text = (
    f"{eliminated_player.get('gameDisplayName')} was eliminated ({eliminated_role})."
    if eliminated_player else "Votes tied. No one was eliminated."
)
```

### All Possible Values:

| Value | Scenario | Currently Set? |
|-------|----------|----------------|
| `"AI"` | AI impostor eliminated | ✅ Line 724 |
| `"Human"` | Human eliminated | ✅ Line 724 |
| `None` | Tie vote, no elimination | ❌ Not explicitly set |

### Recommended Enum:

```python
eliminatedRole: Optional[Literal["AI", "Human"]] = Field(
    None,
    description="Role of eliminated player (None if tie vote)"
)
```

**Note:** Do NOT include `"Tie"` as a string value. Use `None` for no elimination.

---

## 4. Complete Updated Schema

### Recommended `GameResultLastRound` Model:

```python
class GameResultLastRound(BaseModel):
    """Details about the final round and how the game ended."""

    # Player elimination info
    eliminatedPlayer: Optional[str] = Field(
        None,
        description="UID of player eliminated in final round (None if tie vote)"
    )

    eliminatedRole: Optional[Literal["AI", "Human"]] = Field(
        None,
        description="Role of eliminated player (None if tie vote)"
    )

    # Game end condition (for analytics queries)
    endCondition: Literal[
        "all_impostors_eliminated",
        "max_rounds_reached"
    ] = Field(
        ...,
        description="Enum code for how game ended (required)"
    )

    # User-facing messages (for UI display)
    endReasonMessage: str = Field(
        ...,
        description="User-facing explanation of game end"
    )

    # Vote tallies
    voteCounts: dict[str, int] = Field(
        default_factory=dict,
        description="Final round vote tallies {playerId: voteCount}"
    )
```

---

## 5. Components That Need Changes

### 5.1 Backend Changes Required:

#### File: `backend/app/models/game.py`

**Location:** Lines 92-97

**Change:**
```python
# BEFORE
class GameResultLastRound(BaseModel):
    eliminatedPlayer: Optional[str] = Field(None, description="...")
    reason: str = Field(..., description="...")  # ❌ Remove
    voteCounts: dict[str, int] = Field(default_factory=dict, description="...")

# AFTER
class GameResultLastRound(BaseModel):
    eliminatedPlayer: Optional[str] = Field(None, description="...")
    eliminatedRole: Optional[Literal["AI", "Human"]] = Field(None, description="...")  # ✅ Add
    endCondition: Literal["all_impostors_eliminated", "max_rounds_reached"] = Field(..., description="...")  # ✅ Add
    endReasonMessage: str = Field(..., description="...")  # ✅ Add (renamed from reason)
    voteCounts: dict[str, int] = Field(default_factory=dict, description="...")
```

---

#### File: `backend/app/services/game_service.py`

**Location 1:** Lines 745-762 (game end logic in `tally_votes()`)

**Change:**
```python
# BEFORE
if len(active_impostors) == 0:
    update_payload.update({
        "status": "finished",
        "roundPhase": "GAME_ENDED",
        "winner": "humans",
        "ttl": firestore.DELETE_FIELD
    })
    game_is_over = True
    end_reason = "All impostors have been eliminated. Humans win!"  # ❌ Remove

# AFTER
if len(active_impostors) == 0:
    update_payload.update({
        "status": "finished",
        "roundPhase": "GAME_ENDED",
        "winner": "humans",
        "ttl": firestore.DELETE_FIELD
    })
    game_is_over = True
    end_condition = "all_impostors_eliminated"  # ✅ Add enum
    end_reason_message = "All impostors have been eliminated. Humans win!"  # ✅ Renamed
```

```python
# BEFORE
elif current_round >= 3:
    update_payload.update({
        "status": "finished",
        "roundPhase": "GAME_ENDED",
        "winner": "ai",
        "ttl": firestore.DELETE_FIELD
    })
    game_is_over = True
    end_reason = "Maximum rounds reached with surviving impostors. AI win."  # ❌ Remove

# AFTER
elif current_round >= 3:
    update_payload.update({
        "status": "finished",
        "roundPhase": "GAME_ENDED",
        "winner": "ai",
        "ttl": firestore.DELETE_FIELD
    })
    game_is_over = True
    end_condition = "max_rounds_reached"  # ✅ Add enum
    end_reason_message = "Maximum rounds reached with surviving impostors. AI win."  # ✅ Renamed
```

**Location 2:** Lines 785-797 (round_result construction in `tally_votes()`)

**Change:**
```python
# BEFORE
round_result = {
    "round": current_round,
    "totalVotes": len(votes_this_round),
    "votes": votes_summary,
    "eliminatedPlayerId": eliminated_player.get("uid") if eliminated_player else None,
    "eliminatedPlayerName": eliminated_player.get("gameDisplayName") if eliminated_player else None,
    "eliminatedRole": eliminated_role,
    "summary": summary_text,
    "gameEnded": game_is_over,
}

if end_reason:
    round_result["endReason"] = end_reason  # ❌ Remove

# AFTER
round_result = {
    "round": current_round,
    "totalVotes": len(votes_this_round),
    "votes": votes_summary,
    "eliminatedPlayerId": eliminated_player.get("uid") if eliminated_player else None,
    "eliminatedPlayerName": eliminated_player.get("gameDisplayName") if eliminated_player else None,
    "eliminatedRole": eliminated_role,  # ✅ Keep (already exists)
    "summary": summary_text,
    "gameEnded": game_is_over,
}

if game_is_over:
    round_result["endCondition"] = end_condition  # ✅ Add enum
    round_result["endReasonMessage"] = end_reason_message  # ✅ Add message
```

**Location 3:** Lines 645-650 (archive function reads `lastRoundResult`)

**Change:**
```python
# BEFORE
last_round_result_data = game_data.get("lastRoundResult", {})
last_round_result = GameResultLastRound(
    eliminatedPlayer=last_round_result_data.get("eliminatedPlayerId"),
    reason=last_round_result_data.get("endReason", "game_ended"),  # ❌ Remove
    voteCounts=last_round_result_data.get("voteCounts", {})
)

# AFTER
last_round_result_data = game_data.get("lastRoundResult", {})
last_round_result = GameResultLastRound(
    eliminatedPlayer=last_round_result_data.get("eliminatedPlayerId"),
    eliminatedRole=last_round_result_data.get("eliminatedRole"),  # ✅ Add
    endCondition=last_round_result_data.get("endCondition", "max_rounds_reached"),  # ✅ Add with fallback
    endReasonMessage=last_round_result_data.get("endReasonMessage", "Game ended"),  # ✅ Add with fallback
    voteCounts=last_round_result_data.get("voteCounts", {})
)
```

---

### 5.2 Frontend Changes Required:

#### File: `frontend/src/views/GameRoomView.vue`

**Location 1:** Line 91 (reading endReason for phase message)

**Change:**
```javascript
// BEFORE
} else if (phase === 'GAME_ENDED') {
  phaseMessage.value = roundSummary.value?.endReason || 'Game over.';  // ❌ Change
}

// AFTER
} else if (phase === 'GAME_ENDED') {
  phaseMessage.value = roundSummary.value?.endReasonMessage || 'Game over.';  // ✅ Renamed field
}
```

**Location 2:** Line 258 (displaying endReason in template)

**Change:**
```vue
<!-- BEFORE -->
<p v-if="roundSummary.endReason" class="end-reason">{{ roundSummary.endReason }}</p>

<!-- AFTER -->
<p v-if="roundSummary.endReasonMessage" class="end-reason">{{ roundSummary.endReasonMessage }}</p>
```

---

### 5.3 Test File Changes:

#### File: `backend/test_game_archival.py`

**Location:** Line 85-89

**Change:**
```python
# BEFORE
"lastRoundResult": {
    "eliminatedPlayerId": ai_uid,
    "endReason": "All impostors have been eliminated. Humans win!",  # ❌ Change
    "voteCounts": {ai_uid: 3}
}

# AFTER
"lastRoundResult": {
    "eliminatedPlayerId": ai_uid,
    "eliminatedRole": "AI",  # ✅ Add
    "endCondition": "all_impostors_eliminated",  # ✅ Add enum
    "endReasonMessage": "All impostors have been eliminated. Humans win!",  # ✅ Renamed
    "voteCounts": {ai_uid: 3}
}
```

---

## 6. Migration Strategy

### Option A: Breaking Change (Simple, Recommended)

Since you don't have production data yet:

1. Update all code files simultaneously
2. Old `game_rooms` documents in Firestore will fail validation when archived
3. Acceptable because:
   - ✅ No production users yet
   - ✅ Development games expire via TTL anyway
   - ✅ Cleaner than maintaining compatibility

---

### Option B: Backward Compatible (If Needed)

Add fallback logic in archive function:

```python
# Handle both old and new field names
end_condition = last_round_result_data.get("endCondition")
if not end_condition:
    # Fallback: Infer from old endReason field
    old_reason = last_round_result_data.get("endReason", "")
    if "All impostors" in old_reason:
        end_condition = "all_impostors_eliminated"
    else:
        end_condition = "max_rounds_reached"
```

---

## 7. Summary Checklist

### Files to Modify:

- [ ] `backend/app/models/game.py` (GameResultLastRound class)
- [ ] `backend/app/services/game_service.py` (3 locations in tally_votes + archive)
- [ ] `frontend/src/views/GameRoomView.vue` (2 locations)
- [ ] `backend/test_game_archival.py` (mock data)

### New Field Values:

- [ ] `endCondition`: `"all_impostors_eliminated"` | `"max_rounds_reached"`
- [ ] `endReasonMessage`: User-facing string (replaces `reason`)
- [ ] `eliminatedRole`: `"AI"` | `"Human"` | `None`

### Testing Checklist:

- [ ] Play game where AI is eliminated → verify `endCondition = "all_impostors_eliminated"`
- [ ] Play game to round 3 end → verify `endCondition = "max_rounds_reached"`
- [ ] Verify frontend displays `endReasonMessage` correctly
- [ ] Verify archive function writes to `game_results` successfully
- [ ] Verify Pydantic validation passes with new schema

---

**Status:** Complete analysis ready for implementation approval.
