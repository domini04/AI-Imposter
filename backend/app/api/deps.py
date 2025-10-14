from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth
import logging

logger = logging.getLogger(__name__)

# This dependency will look for a "Bearer" token in the Authorization header.
# The tokenUrl is not used for validation here, but it's required by the spec
# and is included in the API docs.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependency to get the current user from a Firebase ID token.

    Validates the token with Firebase and returns the user's UID.
    Raises an HTTP 401 Unauthorized error if the token is invalid or expired.
    """
    logger.info(f"Authenticating user with token: {token[:20]}..." if token else "No token received")

    try:
        # Verify the token against the Firebase Auth service.
        decoded_token = auth.verify_id_token(token)
        # Extract the user's unique ID from the decoded token.
        uid = decoded_token['uid']
        logger.info(f"Successfully authenticated user: {uid}")
        return uid
    except auth.InvalidIdTokenError as e:
        # This error is raised if the token is malformed or invalid.
        logger.error(f"Invalid ID token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.ExpiredIdTokenError as e:
        # This error is raised if the token has expired.
        logger.error(f"Expired token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        # Catch any other potential errors during validation.
        logger.exception(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
