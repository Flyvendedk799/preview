"""Domain verification service for DNS, HTML file, and meta tag methods."""
import dns.resolver
import dns.rdatatype
import requests
from bs4 import BeautifulSoup
from typing import Optional, Tuple
from backend.utils.verification_tokens import create_dns_txt_record, create_html_file_content, create_meta_tag_content


def get_fresh_dns_resolver() -> dns.resolver.Resolver:
    """
    Create a fresh DNS resolver that bypasses caching.
    Uses public DNS servers for more reliable results.
    """
    resolver = dns.resolver.Resolver(configure=False)
    # Use public DNS servers (Cloudflare and Google) for fresh lookups
    resolver.nameservers = ['1.1.1.1', '8.8.8.8', '8.8.4.4', '1.0.0.1']
    resolver.lifetime = 10  # 10 second timeout
    resolver.cache = dns.resolver.Cache(cleaning_interval=0)  # Disable caching
    return resolver


def verify_dns(domain: str, token: str) -> Tuple[bool, Optional[str]]:
    """
    Verify domain ownership via DNS TXT record.
    
    Args:
        domain: Domain name to verify
        token: Verification token
        
    Returns:
        Tuple of (is_verified, error_message)
    """
    try:
        txt_record = create_dns_txt_record(domain, token)
        expected_value = f"preview-verification={token}"
        
        # Create fresh resolver to bypass any caching
        resolver = get_fresh_dns_resolver()
        
        # Query TXT records for the domain
        try:
            answers = resolver.resolve(domain, 'TXT')
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            return False, "DNS record not found or domain does not exist"
        except Exception as e:
            return False, f"DNS lookup error: {str(e)}"
        
        # Check if any TXT record contains our token
        for answer in answers:
            for txt_string in answer.strings:
                txt_str = txt_string.decode('utf-8') if isinstance(txt_string, bytes) else str(txt_string)
                if expected_value in txt_str or token in txt_str:
                    return True, None
        
        return False, "Verification token not found in DNS TXT records"
        
    except Exception as e:
        return False, f"DNS verification error: {str(e)}"


def verify_html_file(domain: str, token: str) -> Tuple[bool, Optional[str]]:
    """
    Verify domain ownership via HTML file upload.
    
    Args:
        domain: Domain name to verify
        token: Verification token
        
    Returns:
        Tuple of (is_verified, error_message)
    """
    try:
        # Construct verification file URL
        url = f"https://{domain}/.preview-verification.txt"
        
        # Fetch the file
        try:
            response = requests.get(url, timeout=6, allow_redirects=True)
            response.raise_for_status()
        except requests.RequestException as e:
            return False, f"Could not fetch verification file: {str(e)}"
        
        # Check content
        expected_content = create_html_file_content(token)
        actual_content = response.text.strip()
        
        if expected_content in actual_content or token in actual_content:
            return True, None
        else:
            return False, "Verification token not found in file content"
            
    except Exception as e:
        return False, f"HTML file verification error: {str(e)}"


def verify_meta_tag(domain: str, token: str) -> Tuple[bool, Optional[str]]:
    """
    Verify domain ownership via meta tag in homepage HTML.
    
    Args:
        domain: Domain name to verify
        token: Verification token
        
    Returns:
        Tuple of (is_verified, error_message)
    """
    try:
        # Fetch homepage
        url = f"https://{domain}/"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=6, allow_redirects=True, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            return False, f"Could not fetch homepage: {str(e)}"
        
        # Parse HTML
        try:
            soup = BeautifulSoup(response.text, 'lxml')
        except Exception as e:
            return False, f"Could not parse HTML: {str(e)}"
        
        # Look for meta tag (case-insensitive)
        meta_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.lower() == 'preview-verification'})
        
        for meta_tag in meta_tags:
            content = meta_tag.get('content', '')
            if token in content:
                return True, None
        
        return False, "Verification meta tag not found in homepage"
        
    except Exception as e:
        return False, f"Meta tag verification error: {str(e)}"


def verify_domain(domain: str, method: str, token: str) -> Tuple[bool, Optional[str]]:
    """
    Verify domain ownership using the specified method.
    
    Args:
        domain: Domain name to verify
        method: Verification method ('dns', 'html', or 'meta')
        token: Verification token
        
    Returns:
        Tuple of (is_verified, error_message)
    """
    if method == 'dns':
        return verify_dns(domain, token)
    elif method == 'html':
        return verify_html_file(domain, token)
    elif method == 'meta':
        return verify_meta_tag(domain, token)
    else:
        return False, f"Unknown verification method: {method}"

