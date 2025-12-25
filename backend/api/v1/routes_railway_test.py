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

