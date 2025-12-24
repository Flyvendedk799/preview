"""Media upload service for R2 storage."""
import os
import uuid
import mimetypes
from datetime import datetime
from typing import Optional, Tuple
import boto3
from botocore.config import Config
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io

from backend.core.config import settings


# Allowed file types and their MIME types
ALLOWED_IMAGE_TYPES = {
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif',
    'image/webp': '.webp',
    'image/svg+xml': '.svg',
}

ALLOWED_DOCUMENT_TYPES = {
    'application/pdf': '.pdf',
}

ALLOWED_TYPES = {**ALLOWED_IMAGE_TYPES, **ALLOWED_DOCUMENT_TYPES}

# Max file sizes
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DOCUMENT_SIZE = 25 * 1024 * 1024  # 25MB


def get_r2_client():
    """Get configured R2 client."""
    if not settings.R2_ACCOUNT_ID:
        return None
    
    return boto3.client(
        's3',
        endpoint_url=f'https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}
        ),
        region_name='auto'
    )


def validate_file(file: UploadFile) -> Tuple[str, str]:
    """
    Validate uploaded file.
    
    Returns:
        Tuple of (mime_type, extension)
    
    Raises:
        HTTPException if validation fails
    """
    # Check content type
    content_type = file.content_type or mimetypes.guess_type(file.filename or '')[0]
    
    if not content_type or content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_TYPES.keys())}"
        )
    
    extension = ALLOWED_TYPES[content_type]
    
    return content_type, extension


async def upload_to_r2(
    file: UploadFile,
    site_id: int,
    folder: str = "media"
) -> dict:
    """
    Upload file to R2 storage.
    
    Args:
        file: The uploaded file
        site_id: Site ID for organization
        folder: Subfolder in bucket (default: "media")
        
    Returns:
        Dict with file info: url, filename, size, mime_type, width, height
    """
    # Validate file
    content_type, extension = validate_file(file)
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Check size limits
    max_size = MAX_IMAGE_SIZE if content_type in ALLOWED_IMAGE_TYPES else MAX_DOCUMENT_SIZE
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {max_size // (1024 * 1024)}MB"
        )
    
    # Generate unique filename
    unique_id = uuid.uuid4().hex[:12]
    timestamp = datetime.utcnow().strftime('%Y%m%d')
    original_name = os.path.splitext(file.filename or 'file')[0]
    # Clean filename
    safe_name = ''.join(c for c in original_name if c.isalnum() or c in '-_')[:50]
    filename = f"{safe_name}_{timestamp}_{unique_id}{extension}"
    
    # Build the key path
    key = f"sites/{site_id}/{folder}/{filename}"
    
    # Get image dimensions if it's an image
    width, height = None, None
    if content_type in ALLOWED_IMAGE_TYPES and content_type != 'image/svg+xml':
        try:
            img = Image.open(io.BytesIO(content))
            width, height = img.size
        except Exception:
            pass
    
    # Upload to R2
    client = get_r2_client()
    
    if client and settings.R2_BUCKET_NAME:
        try:
            client.put_object(
                Bucket=settings.R2_BUCKET_NAME,
                Key=key,
                Body=content,
                ContentType=content_type,
                CacheControl='public, max-age=31536000',  # 1 year cache
            )
            
            # Build public URL
            if settings.R2_PUBLIC_BASE_URL:
                url = f"{settings.R2_PUBLIC_BASE_URL.rstrip('/')}/{key}"
            else:
                url = f"https://{settings.R2_BUCKET_NAME}.r2.cloudflarestorage.com/{key}"
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    else:
        # Fallback for local development - save to local static folder
        local_path = os.path.join('backend', 'static', 'uploads', str(site_id), folder)
        os.makedirs(local_path, exist_ok=True)
        
        file_path = os.path.join(local_path, filename)
        with open(file_path, 'wb') as f:
            f.write(content)
        
        url = f"/static/uploads/{site_id}/{folder}/{filename}"
    
    return {
        'url': url,
        'filename': filename,
        'original_filename': file.filename,
        'size': file_size,
        'mime_type': content_type,
        'width': width,
        'height': height,
    }


async def delete_from_r2(url: str, site_id: int) -> bool:
    """
    Delete file from R2 storage.
    
    Args:
        url: The file URL
        site_id: Site ID for verification
        
    Returns:
        True if deleted successfully
    """
    client = get_r2_client()
    
    if not client or not settings.R2_BUCKET_NAME:
        # Local file deletion
        if url.startswith('/static/uploads/'):
            local_path = os.path.join('backend', url.lstrip('/'))
            if os.path.exists(local_path):
                os.remove(local_path)
                return True
        return False
    
    # Extract key from URL
    if settings.R2_PUBLIC_BASE_URL and url.startswith(settings.R2_PUBLIC_BASE_URL):
        key = url[len(settings.R2_PUBLIC_BASE_URL):].lstrip('/')
    else:
        # Try to extract from standard R2 URL
        try:
            key = url.split('.r2.cloudflarestorage.com/')[-1]
        except:
            return False
    
    # Verify the key belongs to this site
    if not key.startswith(f"sites/{site_id}/"):
        return False
    
    try:
        client.delete_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key
        )
        return True
    except Exception:
        return False

