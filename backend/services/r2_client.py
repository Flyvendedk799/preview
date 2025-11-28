"""Cloudflare R2 storage client using boto3."""
import boto3
from botocore.exceptions import ClientError
from backend.core.config import settings
from backend.services.retry_utils import sync_retry


def get_r2_client():
    """
    Get boto3 S3 client configured for Cloudflare R2.
    
    Returns:
        boto3 S3 client instance
    """
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",  # R2 uses "auto" region
    )


@sync_retry(max_attempts=3, base_delay=1.0, retry_on=(ClientError,))
def upload_file_to_r2(file_bytes: bytes, filename: str, content_type: str) -> str:
    """
    Upload file to Cloudflare R2 and return public URL.
    
    Args:
        file_bytes: File content as bytes
        filename: Object key (path) in R2 bucket
        content_type: MIME type (e.g., "image/png")
        
    Returns:
        Public URL to the uploaded file
        
    Raises:
        ClientError: If upload fails
    """
    client = get_r2_client()
    
    try:
        client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=filename,
            Body=file_bytes,
            ContentType=content_type,
            CacheControl="public, max-age=31536000",  # 1 year cache
        )
        
        # Construct public URL
        # R2 public URLs can be:
        # 1. Custom domain (if R2_PUBLIC_BASE_URL is set to a custom domain)
        # 2. Public dev URL (if R2_PUBLIC_BASE_URL is set to pub-*.r2.dev)
        # 3. Fallback to bucket.account.r2.cloudflarestorage.com (not recommended, requires public access)
        if settings.R2_PUBLIC_BASE_URL:
            # Remove trailing slash and ensure proper URL construction
            base_url = settings.R2_PUBLIC_BASE_URL.rstrip('/')
            public_url = f"{base_url}/{filename}"
        else:
            # Fallback to R2 default URL pattern: bucket.account.r2.cloudflarestorage.com
            # Note: This requires public access to be enabled on the bucket
            public_url = f"https://{settings.R2_BUCKET_NAME}.{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{filename}"
        
        # Log the generated URL for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Generated R2 public URL: {public_url}")
        
        return public_url
    except ClientError as e:
        # Log error without exposing credentials
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error uploading to R2: {type(e).__name__}")
        raise

