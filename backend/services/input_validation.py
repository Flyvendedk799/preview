"""
Comprehensive input validation and sanitization.

FEATURES:
1. URL validation and security checks
2. Request schema validation
3. Data sanitization
4. Rate limit validation
5. Business rule validation
"""
import re
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from pydantic import BaseModel, HttpUrl, validator, Field
from backend.services.observability import StructuredLogger

logger = StructuredLogger("input_validation")


# =============================================================================
# SECURITY VALIDATION
# =============================================================================

class URLSecurityValidator:
    """Comprehensive URL security validation."""

    # Blocked domains (SSRF protection)
    BLOCKED_DOMAINS = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "[::]",
        "::1",
    }

    # Blocked IP ranges (SSRF protection)
    BLOCKED_IP_PATTERNS = [
        r"^10\.",           # Private: 10.0.0.0/8
        r"^172\.(1[6-9]|2[0-9]|3[01])\.",  # Private: 172.16.0.0/12
        r"^192\.168\.",     # Private: 192.168.0.0/16
        r"^169\.254\.",     # Link-local: 169.254.0.0/16
        r"^127\.",          # Loopback: 127.0.0.0/8
    ]

    # Allowed schemes
    ALLOWED_SCHEMES = {"http", "https"}

    # Blocked file extensions
    BLOCKED_EXTENSIONS = {
        ".exe", ".dll", ".bat", ".cmd", ".sh", ".ps1",
        ".scr", ".com", ".pif", ".application", ".gadget",
        ".msi", ".msp", ".cpl", ".jar"
    }

    @classmethod
    def validate(cls, url: str) -> tuple[bool, Optional[str]]:
        """
        Validate URL for security issues.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in cls.ALLOWED_SCHEMES:
                return False, f"Invalid URL scheme: {parsed.scheme}. Only http/https allowed."

            # Check blocked domains
            hostname = parsed.hostname
            if not hostname:
                return False, "URL must have a valid hostname"

            if hostname.lower() in cls.BLOCKED_DOMAINS:
                return False, f"Blocked hostname: {hostname}"

            # Check blocked IP patterns (SSRF protection)
            for pattern in cls.BLOCKED_IP_PATTERNS:
                if re.match(pattern, hostname):
                    return False, f"Private/internal IP addresses not allowed: {hostname}"

            # Check for blocked file extensions
            path_lower = parsed.path.lower()
            for ext in cls.BLOCKED_EXTENSIONS:
                if path_lower.endswith(ext):
                    return False, f"Blocked file extension: {ext}"

            # Check URL length
            if len(url) > 2048:
                return False, "URL too long (max 2048 characters)"

            # Check for suspicious patterns
            if any(char in url for char in ['\n', '\r', '\x00']):
                return False, "URL contains invalid characters"

            return True, None

        except Exception as e:
            return False, f"URL validation error: {str(e)}"

    @classmethod
    def sanitize(cls, url: str) -> str:
        """
        Sanitize URL by removing dangerous characters.

        Args:
            url: URL to sanitize

        Returns:
            Sanitized URL
        """
        # Remove null bytes and newlines
        url = url.replace('\x00', '').replace('\n', '').replace('\r', '')

        # Strip whitespace
        url = url.strip()

        return url


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class DemoPreviewRequestValidated(BaseModel):
    """Validated schema for demo preview requests."""

    url: HttpUrl = Field(
        ...,
        description="URL to generate preview for",
        example="https://example.com"
    )

    # Optional parameters
    force_refresh: bool = Field(
        default=False,
        description="Force refresh and bypass cache"
    )

    timeout: int = Field(
        default=30,
        ge=10,
        le=120,
        description="Timeout in seconds (10-120)"
    )

    @validator('url')
    def validate_url_security(cls, v):
        """Validate URL security."""
        url_str = str(v)

        # Sanitize first
        url_str = URLSecurityValidator.sanitize(url_str)

        # Validate
        is_valid, error_msg = URLSecurityValidator.validate(url_str)
        if not is_valid:
            logger.warning(
                f"URL validation failed: {error_msg}",
                url=url_str[:100],
                error=error_msg
            )
            raise ValueError(error_msg)

        return v

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "force_refresh": False,
                "timeout": 30
            }
        }


class AIAnalysisRequestValidated(BaseModel):
    """Validated schema for AI analysis requests."""

    prompt: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Analysis prompt"
    )

    model: str = Field(
        default="gpt-4o",
        description="AI model to use"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature (0-2)"
    )

    max_tokens: int = Field(
        default=1000,
        ge=100,
        le=4000,
        description="Max tokens to generate"
    )

    @validator('prompt')
    def sanitize_prompt(cls, v):
        """Sanitize prompt."""
        # Remove null bytes
        v = v.replace('\x00', '')

        # Check for suspicious patterns (potential prompt injection)
        suspicious_patterns = [
            r"ignore\s+previous\s+instructions",
            r"system\s*:\s*you\s+are",
            r"<\s*system\s*>",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                logger.warning(
                    "Potentially malicious prompt detected",
                    pattern=pattern,
                    prompt_preview=v[:100]
                )

        return v

    @validator('model')
    def validate_model(cls, v):
        """Validate model name."""
        allowed_models = {"gpt-4o", "gpt-4o-mini", "gpt-4-turbo"}
        if v not in allowed_models:
            raise ValueError(f"Invalid model: {v}. Allowed: {allowed_models}")
        return v


# =============================================================================
# DATA SANITIZATION
# =============================================================================

class DataSanitizer:
    """Utility class for data sanitization."""

    @staticmethod
    def sanitize_string(
        value: str,
        max_length: int = 1000,
        allow_html: bool = False
    ) -> str:
        """
        Sanitize string input.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags

        Returns:
            Sanitized string
        """
        if not value:
            return ""

        # Remove null bytes
        value = value.replace('\x00', '')

        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length]

        # Remove HTML if not allowed
        if not allow_html:
            value = re.sub(r'<[^>]*>', '', value)

        # Normalize whitespace
        value = ' '.join(value.split())

        return value.strip()

    @staticmethod
    def sanitize_dict(
        data: Dict[str, Any],
        allowed_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sanitize dictionary by removing unwanted keys.

        Args:
            data: Dictionary to sanitize
            allowed_keys: List of allowed keys (None = allow all)

        Returns:
            Sanitized dictionary
        """
        if allowed_keys is None:
            return data

        return {
            k: v for k, v in data.items()
            if k in allowed_keys
        }

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal.

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename
        """
        # Remove directory separators
        filename = filename.replace('/', '_').replace('\\', '_')

        # Remove null bytes
        filename = filename.replace('\x00', '')

        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')

        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', '', filename)

        # Ensure not empty
        if not filename:
            filename = "unnamed"

        return filename


# =============================================================================
# BUSINESS RULE VALIDATION
# =============================================================================

class BusinessRuleValidator:
    """Validate business rules and constraints."""

    @staticmethod
    def validate_screenshot_size(width: int, height: int) -> tuple[bool, Optional[str]]:
        """
        Validate screenshot dimensions.

        Args:
            width: Width in pixels
            height: Height in pixels

        Returns:
            Tuple of (is_valid, error_message)
        """
        MIN_DIMENSION = 100
        MAX_DIMENSION = 5000

        if width < MIN_DIMENSION or height < MIN_DIMENSION:
            return False, f"Dimensions too small (min {MIN_DIMENSION}x{MIN_DIMENSION})"

        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            return False, f"Dimensions too large (max {MAX_DIMENSION}x{MAX_DIMENSION})"

        # Check aspect ratio (prevent extremely narrow/wide images)
        aspect_ratio = max(width, height) / min(width, height)
        if aspect_ratio > 10:
            return False, "Aspect ratio too extreme (max 10:1)"

        return True, None

    @staticmethod
    def validate_image_size(size_bytes: int) -> tuple[bool, Optional[str]]:
        """
        Validate image file size.

        Args:
            size_bytes: Size in bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        MAX_SIZE = 10 * 1024 * 1024  # 10 MB

        if size_bytes > MAX_SIZE:
            return False, f"Image too large (max {MAX_SIZE / 1024 / 1024:.1f} MB)"

        if size_bytes < 100:
            return False, "Image too small (min 100 bytes)"

        return True, None

    @staticmethod
    def validate_token_count(token_count: int, max_tokens: int = 100000) -> tuple[bool, Optional[str]]:
        """
        Validate token count for AI requests.

        Args:
            token_count: Number of tokens
            max_tokens: Maximum allowed tokens

        Returns:
            Tuple of (is_valid, error_message)
        """
        if token_count > max_tokens:
            return False, f"Too many tokens (max {max_tokens})"

        if token_count < 1:
            return False, "Token count must be at least 1"

        return True, None


# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def validate_and_sanitize_url(url: str) -> str:
    """
    Validate and sanitize URL.

    Args:
        url: URL to validate

    Returns:
        Sanitized URL

    Raises:
        ValueError: If URL is invalid
    """
    # Sanitize
    url = URLSecurityValidator.sanitize(url)

    # Validate
    is_valid, error_msg = URLSecurityValidator.validate(url)
    if not is_valid:
        raise ValueError(error_msg)

    return url


def validate_request_schema(data: Dict[str, Any], schema: type[BaseModel]) -> BaseModel:
    """
    Validate request data against Pydantic schema.

    Args:
        data: Request data
        schema: Pydantic model schema

    Returns:
        Validated model instance

    Raises:
        ValidationError: If validation fails
    """
    try:
        return schema(**data)
    except Exception as e:
        logger.error(
            f"Request validation failed: {str(e)}",
            schema=schema.__name__,
            error=str(e),
            exc_info=True
        )
        raise
