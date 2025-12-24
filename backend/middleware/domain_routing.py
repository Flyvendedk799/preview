"""Middleware for domain-based routing."""
import logging
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
from backend.db.session import get_db
from backend.services.site_service import get_site_by_domain

logger = logging.getLogger(__name__)


class DomainRoutingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to route requests based on domain.
    
    If the request is for a custom domain (not Railway domain),
    and a site exists for that domain, we ensure proper routing.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Check if request is for a custom domain site.
        """
        host = request.headers.get("host", "")
        
        if host:
            domain_name = host.split(":")[0]
            
            # Check if this is a Railway domain or localhost
            railway_domains = [".railway.app", ".up.railway.app", "localhost", "127.0.0.1"]
            is_railway_domain = any(railway_domain in domain_name for railway_domain in railway_domains)
            
            # If it's not a Railway domain, check if it's a custom domain site
            if not is_railway_domain:
                try:
                    db = next(get_db())
                    try:
                        site = get_site_by_domain(db, domain_name)
                        if site:
                            # This is a custom domain site - let it route through public site routes
                            # The routes will handle it correctly
                            logger.debug(f"Domain routing: {domain_name} -> Site ID {site.id}")
                    except Exception as e:
                        logger.debug(f"Domain routing check failed for {domain_name}: {e}")
                    finally:
                        db.close()
                except Exception as e:
                    logger.warning(f"Error checking domain routing: {e}")
        
        # Continue with normal request processing
        response = await call_next(request)
        return response

