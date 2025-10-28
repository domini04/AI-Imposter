"""
Cloud Function: Archive Game to BigQuery

Triggered by: Firestore onCreate event on game_results collection
Purpose: Streams completed game data to BigQuery for analytics

Deployed to: us-central1 (same region as Firestore)
"""

import functions_framework
from google.cloud import bigquery
from google.events.cloud import firestore
from cloudevents.http import CloudEvent
import logging
from typing import Any, Dict, List

# Initialize clients
bigquery_client = bigquery.Client()
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = 'ai-imposter-6368c'
DATASET_ID = 'game_analytics_dataset'
TABLE_ID = 'game_analytics'


@functions_framework.cloud_event
def archive_game(cloud_event: CloudEvent) -> None:
    """
    Triggered by Firestore onCreate event on game_results collection.
    Archives game data to BigQuery for permanent storage and analysis.

    Args:
        cloud_event: CloudEvent containing Firestore document data
    """
    logger.info(f"Function triggered by event: {cloud_event['id']}")

    try:
        # Extract Firestore document data
        firestore_payload = firestore.DocumentEventData()
        firestore_payload._pb.ParseFromString(cloud_event.data)

        # Get document fields
        document = firestore_payload.value
        fields = document.fields

        # Transform to BigQuery row format
        bq_row = transform_to_bigquery_format(fields)

        # Validate required fields
        required_fields = ['gameId', 'endedAt', 'aiModelUsed', 'winner', 'totalRounds']
        missing = [f for f in required_fields if not bq_row.get(f)]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Insert into BigQuery
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        errors = bigquery_client.insert_rows_json(table_ref, [bq_row])

        if errors:
            logger.error(f"BigQuery insert errors: {errors}")
            raise Exception(f"Failed to insert row: {errors}")

        logger.info(f"✅ Successfully archived game {bq_row['gameId']} to BigQuery")

    except Exception as e:
        logger.exception(f"❌ Error archiving game: {e}")
        raise  # Re-raise to trigger Cloud Functions retry


def transform_to_bigquery_format(fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms Firestore document fields to BigQuery row format.
    Handles Firestore data types (string_value, timestamp_value, etc.)

    Args:
        fields: Firestore document fields from protobuf

    Returns:
        Dictionary in BigQuery row format
    """

    def extract_value(field: Any) -> Any:
        """
        Extract actual value from Firestore field object.
        Handles all Firestore data types recursively.
        """
        if field is None:
            return None

        # String values
        if hasattr(field, 'string_value') and field.string_value:
            return field.string_value

        # Integer values
        if hasattr(field, 'integer_value'):
            return int(field.integer_value)

        # Boolean values
        if hasattr(field, 'boolean_value'):
            return field.boolean_value

        # Timestamp values
        if hasattr(field, 'timestamp_value') and field.timestamp_value:
            # Convert to ISO format string for BigQuery TIMESTAMP
            ts = field.timestamp_value
            return ts.isoformat()

        # Array values (REPEATED fields in BigQuery)
        if hasattr(field, 'array_value') and field.array_value:
            return [extract_value(item) for item in field.array_value.values]

        # Map values (RECORD fields in BigQuery)
        if hasattr(field, 'map_value') and field.map_value:
            return {k: extract_value(v) for k, v in field.map_value.fields.items()}

        # Null value
        if hasattr(field, 'null_value'):
            return None

        return None

    # Build BigQuery row
    row = {
        'gameId': extract_value(fields.get('gameId')),
        'endedAt': extract_value(fields.get('endedAt')),
        'language': extract_value(fields.get('language')),
        'aiModelUsed': extract_value(fields.get('aiModelUsed')),
        'winner': extract_value(fields.get('winner')),
        'totalRounds': extract_value(fields.get('totalRounds')),
        'players': extract_value(fields.get('players')) or [],
        'rounds': extract_value(fields.get('rounds')) or [],
        'votes': extract_value(fields.get('votes')) or [],
        'lastRoundResult': extract_value(fields.get('lastRoundResult')) or {}
    }

    return row
