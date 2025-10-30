import firebase_admin
from firebase_admin import credentials, firestore
import os

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK with environment-aware credential detection.

    - Cloud Run: Uses Application Default Credentials (automatic)
    - Local Dev: Uses service account key file from GOOGLE_APPLICATION_CREDENTIALS
    """

    # Check if running in Cloud Run (K_SERVICE is automatically set by Cloud Run)
    if os.getenv("K_SERVICE"):
        # Running in Cloud Run - use Application Default Credentials
        # No file or env var needed! Cloud Run provides credentials via metadata server
        try:
            firebase_admin.initialize_app()
            print("✅ Firebase initialized with Application Default Credentials (Cloud Run)")
        except Exception as e:
            print(f"❌ Error initializing Firebase with ADC: {e}")
            raise
    else:
        # Running locally - use service account key file
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not cred_path:
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
                "Required for local development. "
                "Set it to the path of your Firebase service account JSON file."
            )

        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized with service account key (Local)")
        except Exception as e:
            print(f"❌ Error initializing Firebase with file: {e}")
            raise

def get_firestore_client():
    """

    Returns an initialized Firestore client.
    Ensures that the Firebase app is initialized before returning the client.
    """
    if not firebase_admin._apps:
        initialize_firebase()
    return firestore.client()

# Example of how to get the client in other parts of the app:
# from .firebase_service import get_firestore_client
# db = get_firestore_client()
