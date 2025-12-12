"""FastAPI application entry point."""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.core.config import settings
from backend.middleware.error_handler import error_handler_middleware
from backend.middleware.security_headers import SecurityHeadersMiddleware
from backend.middleware.request_id import RequestIDMiddleware
from backend.middleware.request_logging import RequestLoggingMiddleware
from backend.utils.logger import setup_logging
from backend.api.v1 import routes_auth, routes_domains, routes_brand, routes_previews, routes_analytics, routes_public_preview, routes_jobs, routes_verification, routes_billing, routes_webhooks, routes_activity, routes_tracking, routes_analytics_extended, routes_organizations, routes_preview_variants, routes_account, routes_blog, routes_preview_debug, routes_newsletter, routes_demo, routes_demo_optimized, routes_health, routes_sitemap
from backend.api.admin import routes_admin

# DEV ONLY: Testing endpoints (disabled in production)
if os.getenv("ENV", "development").lower() != "production":
    from backend.api.v1 import routes_testing
from backend.db import Base
from backend.db.session import engine

# Setup structured logging
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(level=log_level)

# Import all models to ensure they're registered with Base
from backend.models import user, domain, brand, preview, error, activity_log, analytics_event, analytics_aggregate, organization, organization_member, preview_variant, blog_post, newsletter_subscriber  # noqa: F401


# Create database tables on startup
# NOTE: For schema changes going forward, use Alembic migrations (see backend/README_backend.md).
# This create_all() is kept for initial dev setup, but Alembic is the source of truth for evolving schema.
def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API for Preview SaaS Dashboard",
    debug=settings.DEBUG if hasattr(settings, 'DEBUG') else False,
)

# Create tables on startup
@app.on_event("startup")
def on_startup():
    """Initialize database tables on application startup."""
    import logging
    from alembic.config import Config
    from alembic import command
    
    logger = logging.getLogger(__name__)
    
    # Run database migrations automatically on startup (production)
    if os.getenv("ENV", "development").lower() == "production":
        try:
            logger.info("Running database migrations...")
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.error(f"Failed to run database migrations: {e}", exc_info=True)
            # Don't crash the app if migrations fail - log and continue
            # This allows the app to start even if there are migration issues
    
    logger.info("=" * 60)
    logger.info("Starting Preview SaaS API")
    logger.info(f"Environment: {os.getenv('ENV', 'development')}")
    logger.info(f"API Version: {settings.APP_VERSION}")
    logger.info(f"Debug Mode: {settings.DEBUG if hasattr(settings, 'DEBUG') else False}")
    logger.info(f"CORS Origins: {settings.CORS_ALLOWED_ORIGINS if settings.CORS_ALLOWED_ORIGINS else 'All origins (dev mode)'}")
    logger.info("=" * 60)
    
    # Run database migrations automatically on startup (production)
    if os.getenv("ENV", "development").lower() == "production":
        try:
            logger.info("Running database migrations...")
            from alembic.config import Config
            from alembic import command
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migrations completed successfully")
        except Exception as e:
            logger.error(f"Failed to run database migrations: {e}", exc_info=True)
            # Don't crash the app if migrations fail - log and continue
            # This allows the app to start even if there are migration issues
    
    try:
        create_tables()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}", exc_info=True)
        raise


# Configure CORS
# For development: allow all origins for public preview endpoint
# In production, restrict to specific domains
cors_origins = settings.CORS_ALLOWED_ORIGINS.split(",") if settings.CORS_ALLOWED_ORIGINS else []
if cors_origins:
    # Production: restrict to specific origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in cors_origins if origin.strip()],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
else:
    # Development: allow all origins (for public preview endpoint)
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r".*",  # Allow all origins for public preview endpoint (dev only)
        allow_credentials=False,  # Set to False when allowing all origins
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add request ID middleware (first, so all requests have IDs)
app.add_middleware(RequestIDMiddleware)

# Add request logging middleware (after request ID, before security headers)
app.add_middleware(RequestLoggingMiddleware)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Add error handling middleware (should be last)
@app.middleware("http")
async def error_middleware(request: Request, call_next):
    return await error_handler_middleware(request, call_next)

# Mount static files for snippet.js
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Include routers
app.include_router(
    routes_auth.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_domains.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_brand.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_previews.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_analytics.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_public_preview.router,
)
app.include_router(
    routes_sitemap.router,
)
app.include_router(
    routes_jobs.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_verification.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_billing.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_webhooks.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_admin.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_activity.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_tracking.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_analytics_extended.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_organizations.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_preview_variants.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_account.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_blog.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_preview_debug.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_newsletter.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_demo.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_demo_optimized.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    routes_health.router,
    prefix=settings.API_V1_PREFIX,
)

# DEV ONLY: Testing endpoints
if os.getenv("ENV", "development").lower() != "production":
    app.include_router(
        routes_testing.router,
        prefix=settings.API_V1_PREFIX,
    )


@app.get("/health")
def health_check():
    """Health check endpoint."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Health check endpoint called")
    return {"status": "ok", "version": settings.APP_VERSION}


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Preview SaaS API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }

