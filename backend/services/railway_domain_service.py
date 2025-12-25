"""Service for managing Railway custom domains via API."""
import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Railway API endpoint
RAILWAY_API_URL = "https://backboard.railway.app/graphql/v2"

# GraphQL mutation for adding custom domain
ADD_DOMAIN_MUTATION = """
mutation customDomainCreate($input: CustomDomainCreateInput!) {
  customDomainCreate(input: $input) {
    id
    domain
    status
  }
}
"""

# GraphQL query for listing domains
LIST_DOMAINS_QUERY = """
query getService($id: String!) {
  service(id: $id) {
    customDomains {
      id
      domain
      status
    }
  }
}
"""


def get_railway_api_token() -> Optional[str]:
    """
    Get Railway API token from environment.
    
    Checks both RAILWAY_TOKEN (Railway's standard) and RAILWAY_API_TOKEN (for compatibility).
    """
    return os.getenv("RAILWAY_TOKEN") or os.getenv("RAILWAY_API_TOKEN")


def get_railway_service_id() -> Optional[str]:
    """Get Railway service ID from environment."""
    return os.getenv("RAILWAY_SERVICE_ID")


def add_domain_to_railway(domain: str, service_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Add a custom domain to Railway via API.
    
    Args:
        domain: Domain name to add (e.g., "example.com")
        service_id: Railway service ID (optional, uses env var if not provided)
        
    Returns:
        Dict with domain information
        
    Raises:
        ValueError: If Railway API token or service ID is not configured
        requests.RequestException: If API request fails
    """
    api_token = get_railway_api_token()
    if not api_token:
        raise ValueError("RAILWAY_TOKEN or RAILWAY_API_TOKEN environment variable is not set")
    
    service_id = service_id or get_railway_service_id()
    if not service_id:
        raise ValueError("RAILWAY_SERVICE_ID environment variable is not set")
    
    # Get environment ID (optional, Railway may auto-detect)
    environment_id = os.getenv("RAILWAY_ENVIRONMENT_ID")
    
    variables = {
        "input": {
            "domain": domain,
            "serviceId": service_id,
        }
    }
    
    if environment_id:
        variables["input"]["environmentId"] = environment_id
    
    response = requests.post(
        RAILWAY_API_URL,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        json={
            "query": ADD_DOMAIN_MUTATION,
            "variables": variables,
        },
        timeout=30,
    )
    
    response.raise_for_status()
    result = response.json()
    
    if "errors" in result:
        error_messages = [err.get("message", "Unknown error") for err in result["errors"]]
        raise ValueError(f"Railway API error: {', '.join(error_messages)}")
    
    domain_data = result.get("data", {}).get("customDomainCreate")
    if not domain_data:
        raise ValueError("Railway API returned unexpected response format")
    
    logger.info(f"Successfully added domain {domain} to Railway")
    return domain_data


def list_railway_domains(service_id: Optional[str] = None) -> list[Dict[str, Any]]:
    """
    List all custom domains for a Railway service.
    
    Args:
        service_id: Railway service ID (optional, uses env var if not provided)
        
    Returns:
        List of domain dictionaries
        
    Raises:
        ValueError: If Railway API token or service ID is not configured
        requests.RequestException: If API request fails
    """
    api_token = get_railway_api_token()
    if not api_token:
        raise ValueError("RAILWAY_TOKEN or RAILWAY_API_TOKEN environment variable is not set")
    
    service_id = service_id or get_railway_service_id()
    if not service_id:
        raise ValueError("RAILWAY_SERVICE_ID environment variable is not set")
    
    response = requests.post(
        RAILWAY_API_URL,
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        json={
            "query": LIST_DOMAINS_QUERY,
            "variables": {"id": service_id},
        },
        timeout=30,
    )
    
    response.raise_for_status()
    result = response.json()
    
    if "errors" in result:
        error_messages = [err.get("message", "Unknown error") for err in result["errors"]]
        raise ValueError(f"Railway API error: {', '.join(error_messages)}")
    
    service_data = result.get("data", {}).get("service", {})
    return service_data.get("customDomains", [])


def check_domain_exists_in_railway(domain: str, service_id: Optional[str] = None) -> bool:
    """
    Check if a domain already exists in Railway.
    
    Args:
        domain: Domain name to check
        service_id: Railway service ID (optional)
        
    Returns:
        True if domain exists, False otherwise
    """
    try:
        domains = list_railway_domains(service_id)
        return any(d.get("domain") == domain for d in domains)
    except Exception as e:
        logger.warning(f"Error checking domain existence in Railway: {e}")
        return False

