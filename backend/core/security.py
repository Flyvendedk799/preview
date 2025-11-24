"""Security utilities for password hashing and JWT tokens."""
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from backend.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.
    
    Note: bcrypt has a 72-byte limit. Passwords longer than 72 bytes are truncated
    to match the hashing behavior.
    """
    # Ensure password is a string
    if not isinstance(plain_password, str):
        plain_password = str(plain_password)
    
    # Truncate password to 72 bytes (bcrypt limit) to match hashing behavior
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, but ensure we don't break UTF-8 sequences
        truncated = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while truncated and (truncated[-1] & 0xC0) == 0x80:
            truncated = truncated[:-1]
        password_bytes = truncated
        plain_password = password_bytes.decode('utf-8', errors='replace')
    
    # Double-check: re-encode to ensure it's still <= 72 bytes
    password_bytes_check = plain_password.encode('utf-8')
    if len(password_bytes_check) > 72:
        password_bytes_check = password_bytes_check[:72]
        while password_bytes_check and (password_bytes_check[-1] & 0xC0) == 0x80:
            password_bytes_check = password_bytes_check[:-1]
        plain_password = password_bytes_check.decode('utf-8', errors='replace')
    
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password.
    
    Note: bcrypt has a 72-byte limit. Passwords longer than 72 bytes are truncated.
    This is a bcrypt limitation, not a security issue - the first 72 bytes are sufficient.
    """
    # Ensure password is a string
    if not isinstance(password, str):
        password = str(password)
    
    # Truncate password to 72 bytes (bcrypt limit)
    # Encode to bytes to get accurate byte length
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes, but ensure we don't break UTF-8 sequences
        # Find the last valid UTF-8 character boundary within 72 bytes
        truncated = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while truncated and (truncated[-1] & 0xC0) == 0x80:
            truncated = truncated[:-1]
        password_bytes = truncated
    
    # Decode back to string (should be safe now)
    password = password_bytes.decode('utf-8', errors='replace')
    
    # Double-check: re-encode to ensure it's still <= 72 bytes
    # This handles edge cases where decoding might produce a longer string
    password_bytes_check = password.encode('utf-8')
    if len(password_bytes_check) > 72:
        # If somehow still too long, truncate again
        password_bytes_check = password_bytes_check[:72]
        while password_bytes_check and (password_bytes_check[-1] & 0xC0) == 0x80:
            password_bytes_check = password_bytes_check[:-1]
        password = password_bytes_check.decode('utf-8', errors='replace')
    
    # Final verification: ensure password is <= 72 bytes
    final_password_bytes = password.encode('utf-8')
    if len(final_password_bytes) > 72:
        logger.error(
            f"Password still exceeds 72 bytes after truncation: {len(final_password_bytes)} bytes. "
            f"Original length: {len(password_bytes)} bytes"
        )
        # Force truncate one more time as a last resort
        password = password[:72]
        final_password_bytes = password.encode('utf-8')
        if len(final_password_bytes) > 72:
            # If still too long, truncate bytes directly
            password = final_password_bytes[:72].decode('utf-8', errors='replace')
    
    try:
        return pwd_context.hash(password)
    except Exception as e:
        # Log detailed error information for debugging
        logger.error(
            f"Error hashing password: {str(e)}. "
            f"Password type: {type(password)}, "
            f"Password length (chars): {len(password)}, "
            f"Password length (bytes): {len(password.encode('utf-8'))}"
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

