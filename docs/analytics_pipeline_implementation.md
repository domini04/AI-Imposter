# Analytics Pipeline - Step-by-Step Implementation Guide

**Last Updated:** October 16, 2025
**Status:** Phase 1.1 Steps 1-3 Complete, Steps 4-6 In Progress
**Related:** [pipelines_architecture.md](./pipelines_architecture.md)

This document provides detailed, actionable steps to build the Phase 1 Analytics Pipeline. Follow these steps sequentially to achieve a working data pipeline.

---

## Implementation Progress

### Phase 1.1: Foundation
- ✅ **Step 1:** Define game_results schema - COMPLETE
- ⏭️ **Step 2:** Extract chat log function - SKIPPED (feature not implemented)
- ✅ **Step 3:** Archive game results to Firestore - COMPLETE
- ⏳ **Step 4:** Create BigQuery dataset and table - PENDING
- ⏳ **Step 5:** Deploy Cloud Function - PENDING
- ⏳ **Step 6:** End-to-end test - PENDING

### Phase 1.2: Dashboard
- ⏳ Steps 7-9 - Not started

### Phase 1.3: Production Hardening
- ⏳ Steps 10-14 - Not started

---

## Overview

**What You'll Build:**
An automated pipeline that archives every completed game to BigQuery for analysis and visualization.

**Timeline:** 3-5 days
**Prerequisites:**
- ✅ FastAPI backend running
- ✅ Firestore configured
- ✅ Google Cloud Project with billing enabled
- ✅ `gcloud` CLI installed and authenticated

**End State:**
Every finished game automatically appears in BigQuery within 60 seconds, with a Looker Studio dashboard showing AI performance metrics.

---

## Phase 1.1: Foundation (Days 1-2)

**Goal:** Get first game result into BigQuery

### Step 1: Define game_results Schema ✅ COMPLETED

**Task:** Create Pydantic models for the game results data structure.

**Implementation:** `backend/app/models/game.py` (lines 58-124)

Schema models created:
- `GameResultPlayer` - Player information with UID (foreign key), nickname, impostor status, elimination data
- `GameResultAnswer` - Individual answers with playerId (FK), text, and isAI flag
- `GameResultRound` - Round data with question and revealed answers array
- `GameResultVote` - Vote records with voterId (FK), targetId (FK), round, timestamp
- `GameResultLastRound` - Game outcome details (eliminated player, reason, vote counts)
- `GameResult` - Main document structure combining all nested data

**Key Design Decisions:**
- UIDs kept as foreign keys for relational joins (not for user tracking)
- Chat messages removed (feature not implemented yet)
- `isAI` flag added to answers for simplified queries
- All votes backfilled with current timestamp (votes don't currently store timestamps)

**Validation:**
```bash
uv run python -c "from app.models.game import GameResult; print('✓ Schema validated')"
```

**Status:** ✅ Complete - Schema defined and validated

---

### Step 2: ~~Extract Chat Log Function~~ → SKIPPED

**Status:** ⏭️ Skipped - Chat feature not implemented yet

**Rationale:**
The game currently only supports question/answer gameplay without free-form chat between players. The `messages` subcollection contains only round answers, which are extracted differently in Step 3.

**Future Consideration:**
If chat functionality is added later, implement a dedicated chat extraction function that:
- Queries `game_rooms/{gameId}/messages` or separate chat subcollection
- Filters out round answers (which are already captured)
- Includes only conversational messages
- Preserves chronological order with timestamps

---

### Step 3: Archive Game Results to Firestore ✅ COMPLETED

**Task:** Create archival function and integrate with game end logic.

**Implementation:** `backend/app/services/game_service.py`

**Part A: `_archive_game_result()` Helper Function** (lines 523-666)

Created comprehensive extraction and transformation logic:

```python
def _archive_game_result(game_ref, game_data: dict, winner: str):
    """
    Archives finished game to game_results collection for analytics pipeline.
    Fault-tolerant - exceptions logged but not re-raised.
    """
    # Key implementation details:
    # 1. Extracts players from game_data
    # 2. Queries messages subcollection and groups by round
    # 3. Builds rounds with revealedAnswers (includes isAI flag)
    # 4. Extracts votes array (backfills timestamps)
    # 5. Validates with Pydantic GameResult model
    # 6. Writes to game_results collection
```

**Data Extraction Strategy:**
- **Players**: Direct copy from `game_data['players']`
- **Rounds**: Query `messages` subcollection, group by `roundNumber`, match with questions from `game_data['rounds']`
- **Votes**: Extract from `game_data['votes']` array, backfill timestamps
- **Answers**: Cross-reference `senderId` with player list to determine `isAI` flag

**Part B: Conditional Integration** (lines 798-801)

Added to `tally_votes()` function:

```python
game_ref.update(update_payload)

# Archive game results when game ends (round 2 or 3)
if game_is_over:
    winner = update_payload.get("winner")
    _archive_game_result(game_ref, game_data, winner)
```

**Execution Points:**
- ✅ Round 2 ends → All AI eliminated → Archives
- ✅ Round 2 ends → AI >= humans → Archives
- ✅ Round 3 ends → Max rounds reached → Archives
- ❌ Round 2 ends → Game continues → No archive

**Error Handling:**
- Wrapped in try/except to prevent analytics failures from breaking gameplay
- Logs errors with full stack trace for debugging
- TODO noted for future `failed_archives` collection

**Validation:**
```bash
# Play complete game and check Firestore
uv run python -c "from app.services.game_service import _archive_game_result; print('✓ Function imports successfully')"
```

**Status:** ✅ Complete - Archival logic implemented and integrated

---

### Step 4: Create BigQuery Dataset and Table

**Task:** Set up BigQuery infrastructure to receive game data.

**Action 1: Create Dataset**

```bash
# Via gcloud CLI
gcloud config set project ai-imposter-6368c

bq mk --dataset \
  --location=us-central1 \
  --description="AI Impostor Game Analytics Data" \
  ai_imposter_6368c:game_analytics_dataset
```

**Action 2: Create Table Schema File**

Create `backend/bigquery_schema.json`:

```json
[
  {
    "name": "gameId",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Unique identifier for the game"
  },
  {
    "name": "endedAt",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "When the game concluded"
  },
  {
    "name": "language",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Game language (en or ko)"
  },
  {
    "name": "aiModelUsed",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "AI model identifier (e.g., gpt-5)"
  },
  {
    "name": "winner",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Winner of the game (humans or ai)"
  },
  {
    "name": "totalRounds",
    "type": "INTEGER",
    "mode": "REQUIRED",
    "description": "Number of rounds played"
  },
  {
    "name": "endReason",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Reason the game ended"
  },
  {
    "name": "players",
    "type": "RECORD",
    "mode": "REPEATED",
    "description": "Array of player data",
    "fields": [
      {"name": "uid", "type": "STRING", "mode": "REQUIRED"},
      {"name": "gameDisplayName", "type": "STRING", "mode": "REQUIRED"},
      {"name": "isImpostor", "type": "BOOLEAN", "mode": "REQUIRED"},
      {"name": "isEliminated", "type": "BOOLEAN", "mode": "NULLABLE"}
    ]
  },
  {
    "name": "rounds",
    "type": "RECORD",
    "mode": "REPEATED",
    "description": "Array of round data",
    "fields": [
      {"name": "round", "type": "INTEGER", "mode": "REQUIRED"},
      {"name": "question", "type": "STRING", "mode": "REQUIRED"}
    ]
  },
  {
    "name": "messages",
    "type": "RECORD",
    "mode": "REPEATED",
    "description": "Full chat log",
    "fields": [
      {"name": "roundNumber", "type": "INTEGER", "mode": "REQUIRED"},
      {"name": "senderId", "type": "STRING", "mode": "REQUIRED"},
      {"name": "senderName", "type": "STRING", "mode": "REQUIRED"},
      {"name": "text", "type": "STRING", "mode": "REQUIRED"},
      {"name": "timestamp", "type": "TIMESTAMP", "mode": "NULLABLE"}
    ]
  }
]
```

**Action 3: Create Table**

```bash
bq mk --table \
  ai_imposter_6368c:game_analytics_dataset.game_analytics \
  backend/bigquery_schema.json
```

**Validation:**

```bash
# Verify table exists
bq show ai_imposter_6368c:game_analytics_dataset.game_analytics

# Check schema
bq show --schema --format=prettyjson \
  ai_imposter_6368c:game_analytics_dataset.game_analytics
```

---

### Step 5: Create Cloud Function

**Task:** Deploy a Cloud Function that triggers on new `game_results` documents.

**Action 1: Create Function Directory**

```bash
mkdir -p backend/cloud_functions/archive_game
cd backend/cloud_functions/archive_game
```

**Action 2: Create requirements.txt**

```txt
functions-framework==3.*
google-cloud-firestore==2.*
google-cloud-bigquery==3.*
```

**Action 3: Create main.py**

```python
import functions_framework
from google.cloud import bigquery
from google.events.cloud import firestore
import logging
from datetime import datetime

# Initialize clients
bigquery_client = bigquery.Client()
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = 'ai-imposter-6368c'
DATASET_ID = 'game_analytics_dataset'
TABLE_ID = 'game_analytics'

@functions_framework.cloud_event
def archive_game(cloud_event):
    """
    Triggered by Firestore onCreate event on game_results collection.
    Archives game data to BigQuery for permanent storage and analysis.
    """
    logger.info(f"Function triggered by event: {cloud_event['id']}")

    try:
        # Extract Firestore document data
        firestore_payload = firestore.DocumentEventData()
        firestore_payload._pb.ParseFromString(cloud_event.data)

        # Get document fields
        fields = firestore_payload.value.fields

        # Transform to BigQuery row format
        bq_row = transform_to_bigquery_format(fields)

        # Insert into BigQuery
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        errors = bigquery_client.insert_rows_json(table_ref, [bq_row])

        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            raise Exception(f"Failed to insert row: {errors}")

        logger.info(f"Successfully archived game {bq_row['gameId']} to BigQuery")

    except Exception as e:
        logger.exception(f"Error archiving game: {e}")
        raise  # Re-raise to trigger Cloud Functions retry


def transform_to_bigquery_format(fields):
    """
    Transforms Firestore document fields to BigQuery row format.
    Handles Firestore data types (string_value, timestamp_value, etc.)
    """
    def extract_value(field):
        """Extract actual value from Firestore field object."""
        if hasattr(field, 'string_value'):
            return field.string_value
        elif hasattr(field, 'integer_value'):
            return field.integer_value
        elif hasattr(field, 'boolean_value'):
            return field.boolean_value
        elif hasattr(field, 'timestamp_value'):
            # Convert Firestore timestamp to BigQuery TIMESTAMP format
            ts = field.timestamp_value
            return ts.isoformat()
        elif hasattr(field, 'array_value'):
            return [extract_value(item) for item in field.array_value.values]
        elif hasattr(field, 'map_value'):
            return {k: extract_value(v) for k, v in field.map_value.fields.items()}
        return None

    # Build BigQuery row
    row = {
        'gameId': extract_value(fields['gameId']),
        'endedAt': extract_value(fields['endedAt']),
        'language': extract_value(fields['language']),
        'aiModelUsed': extract_value(fields['aiModelUsed']),
        'winner': extract_value(fields['winner']),
        'totalRounds': extract_value(fields['totalRounds']),
        'endReason': extract_value(fields.get('endReason')),
        'players': extract_value(fields.get('players', [])),
        'rounds': extract_value(fields.get('rounds', [])),
        'messages': extract_value(fields.get('messages', []))
    }

    return row
```

**Action 4: Deploy Function**

```bash
gcloud functions deploy archive-game \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=archive_game \
  --trigger-event-filters="type=google.cloud.firestore.document.v1.created" \
  --trigger-event-filters="database=(default)" \
  --trigger-location=us-central1 \
  --trigger-event-filters-path-pattern="document=game_results/{documentId}" \
  --max-instances=10 \
  --timeout=60s \
  --memory=512MB
```

**Validation:**

```bash
# Check deployment status
gcloud functions describe archive-game --region=us-central1

# View logs
gcloud functions logs read archive-game --region=us-central1 --limit=10
```

---

### Step 6: End-to-End Test

**Task:** Verify complete pipeline works from game finish to BigQuery.

**Test Procedure:**

1. **Play a complete game:**
   - Start backend and frontend
   - Create game, add AI players
   - Complete all rounds
   - Finish the game (eliminate AI or reach max rounds)

2. **Check Firestore:**
   ```bash
   # Verify game_results document created
   gcloud firestore documents list game_results --limit 1
   ```

3. **Check Cloud Function Logs:**
   ```bash
   gcloud functions logs read archive-game --region=us-central1 --limit=20
   # Look for "Successfully archived game" message
   ```

4. **Check BigQuery:**
   ```bash
   # Query for the game
   bq query --use_legacy_sql=false \
     'SELECT gameId, endedAt, aiModelUsed, winner
      FROM `ai_imposter_6368c.game_analytics_dataset.game_analytics`
      ORDER BY endedAt DESC
      LIMIT 1'
   ```

5. **Verify Data Integrity:**
   ```bash
   # Check nested arrays populated
   bq query --use_legacy_sql=false \
     'SELECT gameId,
             ARRAY_LENGTH(players) as player_count,
             ARRAY_LENGTH(messages) as message_count
      FROM `ai_imposter_6368c.game_analytics_dataset.game_analytics`
      ORDER BY endedAt DESC
      LIMIT 1'
   ```

**Success Criteria Phase 1.1:**
- ✅ Game result written to `game_results` Firestore collection
- ✅ Cloud Function triggered automatically
- ✅ Data appears in BigQuery within 60 seconds
- ✅ All fields populated correctly (no nulls where unexpected)
- ✅ Nested arrays (players, messages) contain data

---

## Phase 1.2: Dashboard (Days 3-4)

**Goal:** Visualize AI performance metrics

### Step 7: Design Key Metrics Queries

**Task:** Create SQL queries for dashboard visualizations.

**Create file:** `backend/analytics_queries.sql`

```sql
-- Query 1: AI Survival Rate by Model
SELECT
  aiModelUsed,
  COUNT(*) as total_games,
  COUNTIF(winner = 'ai') as ai_wins,
  ROUND(COUNTIF(winner = 'ai') / COUNT(*) * 100, 2) as ai_win_rate_pct
FROM `ai_imposter_6368c.game_analytics_dataset.game_analytics`
GROUP BY aiModelUsed
ORDER BY ai_win_rate_pct DESC;

-- Query 2: Elimination Round Distribution
SELECT
  player.isEliminated,
  COUNT(*) as elimination_count,
  AVG(totalRounds) as avg_round_eliminated
FROM `ai_imposter_6368c.game_analytics_dataset.game_analytics`,
UNNEST(players) as player
WHERE player.isImpostor = TRUE
GROUP BY player.isEliminated;

-- Query 3: Performance Over Time
SELECT
  DATE(endedAt) as game_date,
  aiModelUsed,
  COUNT(*) as games_played,
  ROUND(COUNTIF(winner = 'ai') / COUNT(*) * 100, 2) as win_rate
FROM `ai_imposter_6368c.game_analytics_dataset.game_analytics`
WHERE endedAt >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY game_date, aiModelUsed
ORDER BY game_date DESC, aiModelUsed;

-- Query 4: Human Detection Accuracy
SELECT
  ROUND(COUNTIF(winner = 'humans') / COUNT(*) * 100, 2) as human_detection_rate_pct,
  AVG(totalRounds) as avg_rounds_to_detection
FROM `ai_imposter_6368c.game_analytics_dataset.game_analytics`;

-- Query 5: Language Performance Comparison
SELECT
  language,
  COUNT(*) as total_games,
  ROUND(COUNTIF(winner = 'ai') / COUNT(*) * 100, 2) as ai_success_rate_pct,
  AVG(totalRounds) as avg_rounds
FROM `ai_imposter_6368c.game_analytics_dataset.game_analytics`
GROUP BY language;
```

**Validation:**
Run each query in BigQuery console to verify results make sense.

---

### Step 8: Create Looker Studio Dashboard

**Task:** Build visual dashboard connected to BigQuery.

**Action 1: Open Looker Studio**
1. Go to [Looker Studio](https://lookerstudio.google.com/)
2. Click "Create" → "Report"
3. Select "BigQuery" as data source
4. Choose your project: `ai-imposter-6368c`
5. Select dataset: `game_analytics_dataset`
6. Select table: `game_analytics`
7. Click "Add"

**Action 2: Create Scorecard - AI Win Rate**
1. Add Chart → Scorecard
2. Metric: `Record Count` with filter `winner = 'ai'`
3. Title: "AI Wins"
4. Add second scorecard for total games
5. Create calculated field for win rate:
   ```
   AI Win Rate = (COUNT_DISTINCT(CASE WHEN winner = 'ai' THEN gameId END) / COUNT_DISTINCT(gameId)) * 100
   ```

**Action 3: Create Bar Chart - Win Rate by Model**
1. Add Chart → Bar Chart
2. Dimension: `aiModelUsed`
3. Metric: Calculated field "AI Win Rate"
4. Sort by: AI Win Rate descending
5. Title: "AI Success Rate by Model"

**Action 4: Create Time Series - Performance Over Time**
1. Add Chart → Time Series
2. Dimension: `endedAt` (Date)
3. Breakdown Dimension: `aiModelUsed`
4. Metric: Calculated field "AI Win Rate"
5. Date range: Last 30 days
6. Title: "AI Performance Trends"

**Action 5: Create Table - Detailed Game Log**
1. Add Chart → Table
2. Dimensions: `gameId`, `endedAt`, `aiModelUsed`, `winner`, `totalRounds`, `language`
3. Sort by: `endedAt` descending
4. Rows per page: 10
5. Title: "Recent Games"

**Action 6: Add Filters**
1. Add Control → Drop-down list
2. Control field: `aiModelUsed`
3. Add Control → Date range control
4. Control field: `endedAt`
5. Add Control → Drop-down list
6. Control field: `language`

**Validation:**
- Play 5-10 games with different models
- Refresh dashboard
- Verify metrics update correctly
- Test filters work

---

### Step 9: Generate Test Data

**Task:** Populate dashboard with meaningful data for validation.

**Action: Play Multiple Test Games**

Create a test script to simulate various scenarios:

```python
# backend/scripts/generate_test_games.py
"""
Script to generate test game data for dashboard validation.
Simulates different outcomes to test analytics.
"""

# Scenarios to test:
# 1. GPT-5 wins (AI not detected)
# 2. GPT-5 loses (AI eliminated early)
# 3. GPT-5 loses (AI eliminated late)
# 4. Multiple rounds with different vote patterns
# 5. English vs Korean games

# Run 10 complete games covering all scenarios
```

**Manual Testing:**
Play at least 10 complete games with variations:
- 5 games: GPT-5 model
- 3 games: AI wins
- 7 games: Humans win
- 5 games: English
- 5 games: Korean (if implemented)
- Vary number of rounds (1-3)

**Validation:**
- Dashboard shows at least 10 games
- Win rate calculations correct
- Time series shows daily trends
- Filters work correctly

**Success Criteria Phase 1.2:**
- ✅ Looker Studio dashboard created and connected
- ✅ 5 key visualizations working (scorecards, charts, tables)
- ✅ Filters functional (model, date, language)
- ✅ Dashboard updates within 60 seconds of game completion
- ✅ At least 10 test games successfully visualized

---

## Phase 1.3: Production Hardening (Day 5)

**Goal:** Make pipeline reliable and autonomous

### Step 10: Add Error Handling

**Task:** Implement robust error handling and retry logic.

**Action: Update Cloud Function**

Modify `backend/cloud_functions/archive_game/main.py`:

```python
from google.cloud import firestore as firestore_client

# Add Firestore client for failed_archives
firestore_db = firestore_client.Client()

@functions_framework.cloud_event
def archive_game(cloud_event):
    """Enhanced with error handling and dead letter queue."""

    game_id = None

    try:
        # Extract data
        firestore_payload = firestore.DocumentEventData()
        firestore_payload._pb.ParseFromString(cloud_event.data)
        fields = firestore_payload.value.fields

        # Get game ID for logging
        game_id = extract_value(fields['gameId'])
        logger.info(f"Processing game {game_id}")

        # Transform
        bq_row = transform_to_bigquery_format(fields)

        # Validate required fields
        required_fields = ['gameId', 'endedAt', 'aiModelUsed', 'winner']
        missing = [f for f in required_fields if not bq_row.get(f)]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Insert into BigQuery
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        errors = bigquery_client.insert_rows_json(table_ref, [bq_row])

        if errors:
            logger.error(f"BigQuery errors for game {game_id}: {errors}")
            raise Exception(f"BigQuery insert failed: {errors}")

        logger.info(f"✅ Successfully archived game {game_id}")

    except Exception as e:
        logger.exception(f"❌ Failed to archive game {game_id}: {e}")

        # Write to failed_archives for manual recovery
        try:
            firestore_db.collection('failed_archives').add({
                'gameId': game_id or 'unknown',
                'error': str(e),
                'errorType': type(e).__name__,
                'cloudEventId': cloud_event['id'],
                'timestamp': firestore_client.SERVER_TIMESTAMP,
                'rawData': cloud_event.data.decode('utf-8') if cloud_event.data else None
            })
            logger.info(f"Wrote failed archive record for game {game_id}")
        except Exception as fallback_error:
            logger.error(f"Failed to write to failed_archives: {fallback_error}")

        # Re-raise to trigger Cloud Functions retry
        raise
```

**Redeploy function:**
```bash
cd backend/cloud_functions/archive_game
gcloud functions deploy archive-game \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=archive_game \
  --trigger-event-filters="type=google.cloud.firestore.document.v1.created" \
  --trigger-event-filters="database=(default)" \
  --trigger-location=us-central1 \
  --trigger-event-filters-path-pattern="document=game_results/{documentId}" \
  --max-instances=10 \
  --timeout=60s \
  --memory=512MB \
  --retry  # Enable automatic retries
```

---

### Step 11: Set Up Monitoring

**Task:** Configure Cloud Logging and alerts.

**Action 1: Create Log-Based Metric**

```bash
# Create metric for failed archives
gcloud logging metrics create archive_failures \
  --description="Count of failed game archive attempts" \
  --log-filter='resource.type="cloud_function"
    resource.labels.function_name="archive-game"
    severity>=ERROR'
```

**Action 2: Create Alert Policy**

```bash
# Alert if more than 3 failures in 5 minutes
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Archive Function Failures" \
  --condition-display-name="High error rate" \
  --condition-threshold-value=3 \
  --condition-threshold-duration=300s \
  --condition-filter='metric.type="logging.googleapis.com/user/archive_failures"'
```

**Action 3: Set Up Log Viewer Dashboard**

1. Go to [Cloud Logging](https://console.cloud.google.com/logs)
2. Create saved query:
   ```
   resource.type="cloud_function"
   resource.labels.function_name="archive-game"
   ```
3. Save as "Archive Function Logs"

---

### Step 12: Add TTL to game_results

**Task:** Automatically delete archived game results after 7 days.

**Action:**

Since you already know how to set up TTL:

1. Go to Firebase Console → Firestore
2. Enable TTL on `game_results` collection
3. TTL field: `ttl`
4. Update `_archive_game_result()` to add TTL:

```python
def _archive_game_result(game_ref, game_data, end_reason, eliminated_player, eliminated_role):
    # ... existing code ...

    result_doc = {
        # ... existing fields ...
        'ttl': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    }

    db.collection('game_results').add(result_doc)
```

**Validation:**
- New `game_results` documents have `ttl` field set to 7 days in future
- After 7-8 days, documents are automatically deleted by Firestore

---

### Step 13: Document Operations

**Task:** Create operational runbook for the pipeline.

**Action:** Create `backend/OPERATIONS.md`:

```markdown
# Analytics Pipeline Operations

## Monitoring

**Dashboard:** https://console.cloud.google.com/logs/query?project=ai-imposter-6368c
**Looker Studio:** [URL of your dashboard]

## Common Issues

### Issue: Games not appearing in BigQuery

**Symptoms:** Game finishes but no BigQuery row

**Diagnosis:**
1. Check `game_results` collection - is document created?
2. Check Cloud Function logs for errors
3. Check `failed_archives` collection

**Resolution:**
```bash
# View recent function logs
gcloud functions logs read archive-game --limit=50

# Manual retry from failed_archives
python backend/scripts/retry_failed_archives.py
```

### Issue: Cloud Function timing out

**Symptoms:** Error logs show "Function execution took too long"

**Resolution:**
1. Increase timeout: `--timeout=120s`
2. Check for large message arrays causing slowdown

## Manual Operations

### Retry Failed Archives

```python
# backend/scripts/retry_failed_archives.py
from google.cloud import firestore

db = firestore.Client()
failed = db.collection('failed_archives').stream()

for doc in failed:
    game_id = doc.to_dict()['gameId']
    # Trigger manual retry logic
```

### Backfill Historical Data

If BigQuery table was recreated, backfill from game_results:

```bash
python backend/scripts/backfill_bigquery.py
```
```

---

### Step 14: Final End-to-End Validation

**Task:** Comprehensive system test.

**Test Procedure:**

1. **Normal Flow Test:**
   - Play 3 complete games
   - Verify all appear in BigQuery within 60 seconds
   - Check Looker dashboard updates

2. **Error Handling Test:**
   - Temporarily break BigQuery connection (wrong table name in function)
   - Play a game
   - Verify error logged
   - Verify `failed_archives` document created
   - Fix function and verify retry succeeds

3. **Load Test:**
   - Simulate 5 games finishing within 1 minute
   - Verify all process correctly
   - Check for race conditions or dropped games

4. **Data Integrity Test:**
   - Run SQL query to check for:
     - Null values in required fields
     - Empty arrays where data expected
     - Duplicate gameIds

   ```sql
   -- Check for issues
   SELECT
     gameId,
     CASE
       WHEN aiModelUsed IS NULL THEN 'Missing aiModelUsed'
       WHEN ARRAY_LENGTH(messages) = 0 THEN 'No messages'
       WHEN ARRAY_LENGTH(players) = 0 THEN 'No players'
       ELSE 'OK'
     END as issue
   FROM `ai_imposter_6368c.game_analytics_dataset.game_analytics`
   WHERE aiModelUsed IS NULL
      OR ARRAY_LENGTH(messages) = 0
      OR ARRAY_LENGTH(players) = 0;
   ```

5. **7-Day Autonomous Test:**
   - Let pipeline run for 1 week
   - Play a few games each day
   - Check for any manual interventions needed
   - Verify TTL cleanup working

**Success Criteria Phase 1.3:**
- ✅ Error handling prevents data loss
- ✅ Failed archives written to `failed_archives` collection
- ✅ Cloud Logging alerts configured
- ✅ Operations documentation complete
- ✅ TTL cleanup enabled on `game_results`
- ✅ Pipeline runs 7 days without intervention
- ✅ Zero data loss (all games either in BigQuery or failed_archives)

---

## Checklist: Phase 1 Complete

Use this checklist to verify Phase 1 is fully implemented:

### Infrastructure
- [ ] BigQuery dataset created
- [ ] BigQuery table created with correct schema
- [ ] Cloud Function deployed and connected to Firestore trigger
- [ ] Firestore `game_results` collection structure defined
- [ ] TTL enabled on `game_results` (7-day expiration)
- [ ] `failed_archives` collection exists

### Code
- [ ] `GameResult` model defined in backend
- [ ] `_extract_full_chat_log()` function implemented
- [ ] `_archive_game_result()` function implemented
- [ ] `tally_votes()` updated to call archive function
- [ ] Cloud Function has error handling and retry logic

### Monitoring
- [ ] Cloud Logging configured
- [ ] Log-based metrics created
- [ ] Alert policies configured
- [ ] Looker Studio dashboard created with 5+ visualizations
- [ ] Dashboard filters working (model, date, language)

### Documentation
- [ ] BigQuery schema documented
- [ ] SQL queries for analytics documented
- [ ] Operations runbook created
- [ ] Testing procedures documented

### Validation
- [ ] End-to-end test passed (game → Firestore → BigQuery)
- [ ] Dashboard shows live data
- [ ] Error handling tested (failed archives work)
- [ ] Performance acceptable (<60s latency)
- [ ] 7-day autonomous operation successful

---

## Troubleshooting Guide

### Cloud Function Not Triggering

**Check 1:** Verify trigger configuration
```bash
gcloud functions describe archive-game --region=us-central1 | grep trigger
```

**Check 2:** Test manually
```bash
# Create test game_results document
gcloud firestore documents create game_results/test_doc_$(date +%s) \
  --data='{"gameId":"test","endedAt":"2025-10-14T10:00:00Z","language":"en","aiModelUsed":"gpt-5","winner":"ai","totalRounds":1}'

# Check if function triggered
gcloud functions logs read archive-game --limit=10
```

### BigQuery Insert Failures

**Check 1:** Schema mismatch
```bash
# Compare actual data vs schema
bq show --schema ai_imposter_6368c:game_analytics_dataset.game_analytics
```

**Check 2:** Quota exceeded
```bash
gcloud logging read "resource.type=cloud_function AND textPayload=~'quota'"
```

### Dashboard Not Updating

**Check 1:** BigQuery data refresh
- Looker Studio refreshes every 15 minutes by default
- Force refresh: Dashboard → Resource → Manage added data sources → Refresh

**Check 2:** Date range filter
- Ensure date range filter includes recent games

---

## Next Steps After Phase 1

Once Phase 1 is complete and validated:

1. **Run for 2 weeks** - Collect meaningful data from real playtests
2. **Analyze insights** - Look for patterns in AI detection
3. **Iterate on prompts** - Use data to improve AI behavior
4. **Evaluate Phase 2** - Decide if training pipeline ROI is worth it

**Phase 2 Prerequisites:**
- 100+ games in BigQuery
- Clear patterns identified
- Budget allocated for ML training

---

**Document Status:** Implementation guide complete. Ready to execute Phase 1.1.
