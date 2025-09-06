import sys
from pathlib import Path

# Add the project root to the Python path
# This is necessary to ensure that the `app` module can be found
# when running this script from the project root.
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from app.services.firebase_service import get_firestore_client
from google.cloud.firestore_v1.base_client import BaseClient

def test_firebase_connection():
    """
    Initializes Firebase and performs a test write/read/delete operation.
    """
    print("--- Testing Firebase Connection ---")
    
    # Load environment variables from .env file in the project root
    project_root_for_env = project_root.parent
    env_path = project_root_for_env / '.env'
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        print("Please ensure the .env file is in the project root directory (outside of 'backend').")
        return
        
    load_dotenv(dotenv_path=env_path)
    print("Attempting to load environment variables from .env file...")

    try:
        print("Initializing Firestore client...")
        db: BaseClient = get_firestore_client()
        print("Firestore client initialized successfully.")
        
        # 1. Create a test document
        print("Step 1: Creating a test document in 'test_collection'...")
        doc_ref = db.collection('test_collection').document('connection_test')
        doc_ref.set({
            'status': 'success',
            'timestamp': 'now' # Using a static string for simplicity
        })
        print("Step 1: Successfully created test document.")

        # 2. Read the test document
        print("Step 2: Reading the test document...")
        doc = doc_ref.get()
        if doc.exists:
            print(f"Step 2: Successfully read document data: {doc.to_dict()}")
        else:
            raise Exception("Failed to read the document that was just created.")
            
        # 3. Delete the test document
        print("Step 3: Deleting the test document...")
        doc_ref.delete()
        print("Step 3: Successfully deleted test document.")
        
        print("\n✅ --- Firebase Connection Test Successful! ---")
        
    except Exception as e:
        print(f"\n❌ --- Firebase Connection Test Failed! ---")
        print(f"An error occurred: {e}")
        print("Please check the following:")
        print("1. Your GOOGLE_APPLICATION_CREDENTIALS path in the .env file is correct.")
        print("2. The service account has the 'Cloud Datastore User' or 'Editor' role in GCP.")
        print("3. Firestore is enabled and in the correct mode (Native or Datastore) for your project.")

if __name__ == "__main__":
    test_firebase_connection()
