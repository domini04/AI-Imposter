import firebase_admin
from firebase_admin import credentials, firestore
import os

def initialize_firebase():
    """
    Initializes the Firebase Admin SDK using credentials from environment variables.
    This function should be called once when the FastAPI application starts.
    """
    # The GOOGLE_APPLICATION_CREDENTIALS environment variable should be set to the
    # path of your Firebase service account key JSON file.
    # This is the standard and most secure way to authenticate server-side applications.
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if not cred_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")

    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")
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
