from dotenv import load_dotenv
from pathlib import Path
import os

def load_environment_variables():
    """
    Loads environment variables from a .env file located in the project root.
    """
    current_file_path = Path(__file__).resolve()

    # Walk up the directory tree (core -> app -> backend -> project root, ...)
    env_path = None
    search_dirs = [current_file_path.parent] + list(current_file_path.parents)
    for directory in search_dirs:
        candidate = directory / ".env"
        if candidate.exists():
            env_path = candidate
            break

    if env_path is None:
        print("Warning: .env file not found while attempting to load environment variables")
        return

    print(f"Loading environment variables from: {env_path}")
    # load_dotenv will not override existing environment variables.
    load_dotenv(dotenv_path=env_path)

# Automatically load environment variables when this module is imported.
load_environment_variables()
