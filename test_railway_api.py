"""Test script to verify Railway API credentials."""
import os
import sys
import requests
from typing import Optional

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


def get_env_var(name: str) -> Optional[str]:
    """Get environment variable or prompt user."""
    value = os.getenv(name)
    if not value:
        print(f"[ERROR] {name} not found in environment variables")
        print(f"   Please set it in Railway Dashboard -> Backend Service -> Variables")
        return None
    return value


def test_railway_api():
    """Test Railway API credentials."""
    print("[TEST] Testing Railway API Credentials...\n")
    
    # Get credentials
    api_token = get_env_var("RAILWAY_API_TOKEN")
    service_id = get_env_var("RAILWAY_SERVICE_ID")
    
    if not api_token or not service_id:
        print("\n[ERROR] Missing required environment variables!")
        print("\nRequired variables:")
        print("  - RAILWAY_API_TOKEN")
        print("  - RAILWAY_SERVICE_ID")
        sys.exit(1)
    
    print(f"[OK] RAILWAY_API_TOKEN: Found (length: {len(api_token)})")
    print(f"[OK] RAILWAY_SERVICE_ID: Found ({service_id[:8]}...{service_id[-8:]})")
    print()
    
    # Test API connection
    print("[TEST] Testing API connection...")
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
        result = response.json()
        
        # Check for GraphQL errors
        if "errors" in result:
            errors = result["errors"]
            print(f"\n[ERROR] Railway API returned errors:")
            for error in errors:
                print(f"   - {error.get('message', 'Unknown error')}")
            
            # Check for common error types
            error_messages = [err.get("message", "").lower() for err in errors]
            if "unauthorized" in " ".join(error_messages) or "invalid token" in " ".join(error_messages):
                print("\n[TIP] This usually means:")
                print("   - Your API token is invalid or expired")
                print("   - Try creating a new token in Railway Dashboard -> Settings -> API Tokens")
            elif "not found" in " ".join(error_messages) or "service" in " ".join(error_messages):
                print("\n[TIP] This usually means:")
                print("   - Your Service ID is incorrect")
                print("   - Check the Service ID in Railway Dashboard -> Backend Service -> Settings")
            
            sys.exit(1)
        
        # Success!
        service_data = result.get("data", {}).get("service")
        if not service_data:
            print("\n[ERROR] Unexpected response format from Railway API")
            print(f"   Response: {result}")
            sys.exit(1)
        
        print("\n[SUCCESS] Railway API credentials are valid!\n")
        print(f"[INFO] Service Information:")
        print(f"   Name: {service_data.get('name', 'N/A')}")
        print(f"   ID: {service_data.get('id', 'N/A')}")
        print(f"   Project ID: {service_data.get('projectId', 'N/A')}")
        
        custom_domains = service_data.get("customDomains", [])
        print(f"\n[INFO] Custom Domains: {len(custom_domains)}")
        if custom_domains:
            for domain in custom_domains:
                status = domain.get("status", "unknown")
                domain_name = domain.get("domain", "N/A")
                status_icon = "[OK]" if status == "active" else "[PENDING]" if status == "pending" else "[ERROR]"
                print(f"   {status_icon} {domain_name} ({status})")
        else:
            print("   No custom domains configured yet")
        
        print("\n[SUCCESS] Your Railway API setup is working correctly!")
        print("   Domains will be automatically added when users create them in your platform.")
        
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] Network error connecting to Railway API:")
        print(f"   {str(e)}")
        print("\n[TIP] Check your internet connection and try again")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error:")
        print(f"   {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    test_railway_api()

