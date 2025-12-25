"""Test endpoint for Railway API credentials."""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import os
import requests
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/railway-test", tags=["railway-test"])

# Railway API endpoint
RAILWAY_API_URL = "https://backboard.railway.app/graphql/v2"

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
    
    This endpoint verifies that RAILWAY_API_TOKEN and RAILWAY_SERVICE_ID
    are correctly configured and can access the Railway API.
    
    Returns:
        Dict with test results and service information
    """
    # Get credentials
    api_token = os.getenv("RAILWAY_API_TOKEN")
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
        result["error"] = "RAILWAY_API_TOKEN not found in environment variables"
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
        simple_query = """
        query {
            me {
                id
                email
            }
        }
        """
        
        # Try simple query first
        response = requests.post(
            RAILWAY_API_URL,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
            json={
                "query": simple_query,
            },
            timeout=10,
        )
        
        # Log response for debugging
        logger.info(f"Railway API response status: {response.status_code}")
        logger.info(f"Railway API response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            # Try to get error details
            try:
                error_data = response.json()
                result["error"] = f"Railway API returned {response.status_code}: {error_data}"
            except:
                result["error"] = f"Railway API returned {response.status_code}: {response.text[:500]}"
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
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
                    "This usually means:\n"
                    "1. Your API token is invalid or expired\n"
                    "2. The token doesn't have the required permissions\n"
                    "3. You need to create a new token\n\n"
                    "To fix:\n"
                    "1. Go to Railway Dashboard -> Settings -> API Tokens\n"
                    "2. Delete the old token (if exists)\n"
                    "3. Create a new token\n"
                    "4. Copy it immediately (you won't see it again)\n"
                    "5. Update RAILWAY_API_TOKEN in Railway environment variables\n"
                    "6. Redeploy your service"
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

