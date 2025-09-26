from dotenv import load_dotenv
from pathlib import Path
import os

def load_environment_variables():
    """
    Loads environment variables from a .env file located in the project root.
    """
    # The path to this file (config.py)
    current_file_path = Path(__file__)
    # The path to the backend/app/core directory
    core_dir = current_file_path.parent
    # The path to the project root (3 levels up from core_dir)
    project_root = core_dir.parent.parent.parent
    # The full path to the .env file
    env_path = project_root / ".env"

    if env_path.exists():
        print(f"Loading environment variables from: {env_path}")
        # load_dotenv will not override existing environment variables.
        load_dotenv(dotenv_path=env_path)
    else:
        print(f"Warning: .env file not found at {env_path}")

# Automatically load environment variables when this module is imported.
load_environment_variables()
