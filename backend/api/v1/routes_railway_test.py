"""Test endpoint for Railway API credentials."""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import os
import requests
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/railway-test", tags=["railway-test"])

# Railway API endpoint
# Note: Railway uses backboard.railway.com (not .app) for their GraphQL API
RAILWAY_API_URL = "https://backboard.railway.com/graphql/v2"

# GraphQL query to test API access
TEST_QUERY = """
query getService($id: String!) {
  service(id: $id) {
    id
    name
    projectId
    customDomains {
      id
      domain
      status
    }
  }
}
"""


@router.get("", response_model=Dict[str, Any])
def test_railway_api_credentials():
    """
    Test Railway API credentials.
    
    This endpoint verifies that RAILWAY_TOKEN (or RAILWAY_API_TOKEN) and RAILWAY_SERVICE_ID
    are correctly configured and can access the Railway API.
    
    Returns:
        Dict with test results and service information
    """
    # Get credentials - Railway uses RAILWAY_TOKEN, but we also check RAILWAY_API_TOKEN for compatibility
    api_token = os.getenv("RAILWAY_TOKEN") or os.getenv("RAILWAY_API_TOKEN")
    service_id = os.getenv("RAILWAY_SERVICE_ID")
    
    result = {
        "credentials_configured": False,
        "api_connection": False,
        "service_found": False,
        "error": None,
        "service_info": None,
        "custom_domains": [],
    }
    
    # Check if credentials are set
    if not api_token:
        result["error"] = "RAILWAY_TOKEN or RAILWAY_API_TOKEN not found in environment variables"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    
    if not service_id:
        result["error"] = "RAILWAY_SERVICE_ID not found in environment variables"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    
    result["credentials_configured"] = True
    
    # Test API connection
    try:
        # First try a simple query to test authentication
        # Railway's GraphQL API might require account tokens, not project tokens
        simple_query = """
        query {
            me {
                id
                email
            }
        }
        """
        
        # Try with Bearer token (standard GraphQL API format)
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        
        # Log token info (first/last few chars for debugging, not full token)
        token_preview = f"{api_token[:8]}...{api_token[-8:]}" if len(api_token) > 16 else "***"
        logger.info(f"Testing Railway API with token: {token_preview}")
        logger.info(f"Service ID: {service_id}")
        
        response = requests.post(
            RAILWAY_API_URL,
            headers=headers,
            json={
                "query": simple_query,
            },
            timeout=10,
        )
        
        # Log full response for debugging
        logger.info(f"Railway API response status: {response.status_code}")
        logger.info(f"Railway API response headers: {dict(response.headers)}")
        try:
            logger.info(f"Railway API response body: {response.text[:500]}")
        except:
            pass
        
        if response.status_code != 200:
            # Try to get error details
            try:
                error_data = response.json()
                result["error"] = f"Railway API returned {response.status_code}: {error_data}"
            except:
                result["error"] = f"Railway API returned {response.status_code}: {response.text[:500]}"
            
            # Provide specific guidance based on status code
            if response.status_code == 401 or response.status_code == 403:
                result["error"] += (
                    "\n\nIMPORTANT: Railway's GraphQL API requires an ACCOUNT TOKEN, not a PROJECT TOKEN.\n"
                    "Your current token (727141c1-4827-475d-b4ef-fca188ef459c) appears to be a Project Token.\n\n"
                    "To fix:\n"
                    "1. Go to Railway Dashboard -> Account Settings -> API Tokens\n"
                    "2. Create an ACCOUNT TOKEN (not Project Token)\n"
                    "3. Account tokens have access to all projects\n"
                    "4. Set it as RAILWAY_API_TOKEN\n"
                    "5. Redeploy\n\n"
                    "OR use manual domain addition (recommended):\n"
                    "Railway Dashboard -> Backend Service -> Settings -> Networking -> Add Custom Domain"
                )
            
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE if response.status_code != 401 else status.HTTP_401_UNAUTHORIZED,
                detail=result["error"]
            )
        
        api_result = response.json()
        
        # Check for GraphQL errors in simple query
        if "errors" in api_result:
            errors = api_result["errors"]
            error_messages = [err.get("message", "Unknown error") for err in errors]
            error_text = "; ".join(error_messages)
            
            if "not authorized" in error_text.lower() or "unauthorized" in error_text.lower():
                result["error"] = (
                    f"Authentication failed: {error_text}\n\n"
                    "IMPORTANT FINDING:\n"
                    "Railway's public GraphQL API does NOT support domain management.\n"
                    "The `customDomainCreate` mutation is not available in their public API.\n\n"
                    "Even with a valid Account Token, domain management via API is not possible.\n\n"
                    "RECOMMENDED SOLUTION: Manual Domain Addition\n"
                    "1. User creates domain in your platform ✅\n"
                    "2. Add domain manually:\n"
                    "   Railway Dashboard -> Backend Service -> Settings -> Networking\n"
                    "   -> Add Custom Domain\n"
                    "3. Railway provisions SSL automatically ✅\n\n"
                    "This is the only reliable way to add custom domains to Railway."
                )
            else:
                result["error"] = f"Authentication test failed: {error_text}"
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["error"]
            )
        
        # If simple query works, try the service query
        response = requests.post(
            RAILWAY_API_URL,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
            json={
                "query": TEST_QUERY,
                "variables": {"id": service_id},
            },
            timeout=10,
        )
        
        logger.info(f"Service query response status: {response.status_code}")
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                result["error"] = f"Service query failed ({response.status_code}): {error_data}"
            except:
                result["error"] = f"Service query failed ({response.status_code}): {response.text[:500]}"
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=result["error"]
            )
        
        response.raise_for_status()
        api_result = response.json()
        
        # Check for GraphQL errors
        if "errors" in api_result:
            errors = api_result["errors"]
            error_messages = [err.get("message", "Unknown error") for err in errors]
            result["error"] = "; ".join(error_messages)
            
            # Provide helpful error messages
            error_text = " ".join(error_messages).lower()
            if "unauthorized" in error_text or "invalid token" in error_text:
                result["error"] += " (API token is invalid or expired. Create a new token in Railway Dashboard -> Settings -> API Tokens)"
            elif "not found" in error_text:
                result["error"] += " (Service ID is incorrect. Check Railway Dashboard -> Backend Service -> Settings)"
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["error"]
            )
        
        result["api_connection"] = True
        
        # Get service data
        service_data = api_result.get("data", {}).get("service")
        if not service_data:
            result["error"] = "Unexpected response format from Railway API"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        result["service_found"] = True
        result["service_info"] = {
            "id": service_data.get("id"),
            "name": service_data.get("name"),
            "project_id": service_data.get("projectId"),
        }
        
        # Get custom domains
        custom_domains = service_data.get("customDomains", [])
        result["custom_domains"] = [
            {
                "id": domain.get("id"),
                "domain": domain.get("domain"),
                "status": domain.get("status"),
            }
            for domain in custom_domains
        ]
        
        return result
        
    except requests.exceptions.RequestException as e:
        result["error"] = f"Network error: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=result["error"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error testing Railway API")
        result["error"] = f"Unexpected error: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )

