# Archive Game Cloud Function

## Purpose

Automatically streams completed game data from Firestore to BigQuery for analytics.

## Trigger

- **Event:** Firestore document created
- **Collection:** `game_results`
- **Region:** us-central1

## Flow

```
Game ends
    ↓
Backend writes to: firestore://game_results/{gameId}
    ↓
Cloud Function triggers automatically
    ↓
Transforms Firestore document → BigQuery row
    ↓
Inserts into: bigquery://ai-imposter-6368c.game_analytics_dataset.game_analytics
```

## Deployment

From the project root:

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
  --memory=512MB
```

## Local Testing

Cannot test locally - requires Firestore trigger infrastructure. Test by:

1. Playing a complete game
2. Checking Cloud Function logs: `gcloud functions logs read archive-game --region=us-central1 --limit=20`
3. Querying BigQuery: `bq query "SELECT * FROM game_analytics_dataset.game_analytics ORDER BY endedAt DESC LIMIT 1"`

## Monitoring

View logs:
```bash
gcloud functions logs read archive-game --region=us-central1 --limit=50
```

View function details:
```bash
gcloud functions describe archive-game --region=us-central1
```

## Cost

- ~$0.10/month for 1000 game completions
- Charged per invocation + execution time
- Free tier: 2M invocations/month

## Dependencies

- `functions-framework` - Cloud Functions runtime
- `google-cloud-bigquery` - BigQuery client library
