"""Verification token generation and instruction utilities."""
import secrets
from typing import Dict


def generate_verification_token() -> str:
    """
    Generate a cryptographically random verification token.
    
    Returns:
        Random token string (~32 characters)
    """
    return secrets.token_urlsafe(24)  # ~32 characters when URL-safe encoded


def create_dns_txt_record(domain: str, token: str) -> str:
    """
    Generate DNS TXT record value for verification.
    
    Args:
        domain: Domain name
        token: Verification token
        
    Returns:
        TXT record value string
    """
    return f"preview-verification={token}"


def get_dns_instructions(domain: str, token: str) -> Dict[str, str]:
    """
    Get DNS verification instructions.
    
    Args:
        domain: Domain name
        token: Verification token
        
    Returns:
        Dictionary with instructions
    """
    txt_record = create_dns_txt_record(domain, token)
    return {
        "method": "dns",
        "token": token,
        "txt_record": txt_record,
        "instructions": f"Add a TXT record to your DNS settings:\n\nName: @ (or {domain})\nValue: {txt_record}\n\nAfter adding the record, wait 30-60 seconds for DNS propagation, then click 'Check Verification'."
    }


def create_html_file_content(token: str) -> str:
    """
    Generate HTML file content for verification.
    
    Args:
        token: Verification token
        
    Returns:
        File content string
    """
    return f"preview-verification={token}"


def get_html_file_instructions(domain: str, token: str) -> Dict[str, str]:
    """
    Get HTML file verification instructions.
    
    Args:
        domain: Domain name
        token: Verification token
        
    Returns:
        Dictionary with instructions
    """
    file_content = create_html_file_content(token)
    return {
        "method": "html",
        "token": token,
        "file_content": file_content,
        "file_name": ".preview-verification.txt",
        "instructions": f"Create a file named '.preview-verification.txt' in your website's root directory (same location as index.html) with the following content:\n\n{file_content}\n\nThe file should be accessible at: https://{domain}/.preview-verification.txt\n\nAfter uploading, click 'Check Verification'."
    }


def create_meta_tag_content(token: str) -> str:
    """
    Generate meta tag HTML for verification.
    
    Args:
        token: Verification token
        
    Returns:
        Meta tag HTML string
    """
    return f'<meta name="preview-verification" content="{token}">'


def get_meta_tag_instructions(domain: str, token: str) -> Dict[str, str]:
    """
    Get meta tag verification instructions.
    
    Args:
        domain: Domain name
        token: Verification token
        
    Returns:
        Dictionary with instructions
    """
    meta_tag = create_meta_tag_content(token)
    return {
        "method": "meta",
        "token": token,
        "meta_tag": meta_tag,
        "instructions": f"Add the following meta tag to the <head> section of your homepage (index.html or equivalent):\n\n{meta_tag}\n\nThe tag should be on the page accessible at: https://{domain}/\n\nAfter adding the tag, click 'Check Verification'."
    }

