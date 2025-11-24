"""Security utilities for password hashing and JWT tokens."""
import logging
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from backend.core.config import settings

logger = logging.getLogger(__name__)


def _truncate_password_to_72_bytes(password: str) -> bytes:
    """
    Truncate password to 72 bytes (bcrypt limit) ensuring valid UTF-8.
    Returns bytes representation.
    """
    if not isinstance(password, str):
        password = str(password)
    
    password_bytes = password.encode('utf-8')
    if len(password_bytes) <= 72:
        return password_bytes
    
    # Truncate to 72 bytes, but ensure we don't break UTF-8 sequences
    truncated = password_bytes[:72]
    # Remove any incomplete UTF-8 sequences at the end
    while truncated and (truncated[-1] & 0xC0) == 0x80:
        truncated = truncated[:-1]
    
    return truncated


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.
    
    Note: bcrypt has a 72-byte limit. Passwords longer than 72 bytes are truncated
    to match the hashing behavior.
    """
    try:
        # Truncate password to 72 bytes (bcrypt limit)
        password_bytes = _truncate_password_to_72_bytes(plain_password)
        
        # Convert hashed_password to bytes if it's a string (from database)
        if isinstance(hashed_password, str):
            hashed_bytes = hashed_password.encode('utf-8')
        else:
            hashed_bytes = hashed_password
        
        # Use bcrypt directly to avoid passlib initialization issues
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}", exc_info=True)
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt.
    
    Note: bcrypt has a 72-byte limit. Passwords longer than 72 bytes are truncated.
    This is a bcrypt limitation, not a security issue - the first 72 bytes are sufficient.
    """
    try:
        # Truncate password to 72 bytes (bcrypt limit)
        password_bytes = _truncate_password_to_72_bytes(password)
        
        # Use bcrypt directly to avoid passlib initialization issues
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string (bcrypt hash is ASCII-safe)
        return hashed.decode('utf-8')
    except Exception as e:
        # Log detailed error information for debugging
        logger.error(
            f"Error hashing password: {str(e)}. "
            f"Password type: {type(password)}, "
            f"Password length (chars): {len(password) if isinstance(password, str) else 'N/A'}, "
            f"Password length (bytes): {len(password.encode('utf-8')) if isinstance(password, str) else 'N/A'}"
        )
        raise


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """Decode a JWT token and return the email."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None

