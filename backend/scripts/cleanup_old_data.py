"""Cleanup script for old data retention."""
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.models.preview_variant import PreviewVariant
from backend.models.analytics_event import AnalyticsEvent
from backend.models.preview_job_failure import PreviewJobFailure
from backend.utils.logger import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Retention periods (in days)
PREVIEW_VARIANT_RETENTION_DAYS = int(os.getenv("PREVIEW_VARIANT_RETENTION_DAYS", "365"))  # 1 year
ANALYTICS_EVENT_RETENTION_DAYS = int(os.getenv("ANALYTICS_EVENT_RETENTION_DAYS", "90"))  # 3 months
JOB_FAILURE_RETENTION_DAYS = int(os.getenv("JOB_FAILURE_RETENTION_DAYS", "30"))  # 30 days


def cleanup_preview_variants(db: Session, days: int):
    """Delete preview variants older than specified days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted = db.query(PreviewVariant).filter(
        PreviewVariant.created_at < cutoff_date
    ).delete()
    db.commit()
    logger.info(f"Deleted {deleted} preview variants older than {days} days")
    return deleted


def cleanup_analytics_events(db: Session, days: int):
    """Delete analytics events older than specified days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.created_at < cutoff_date
    ).delete()
    db.commit()
    logger.info(f"Deleted {deleted} analytics events older than {days} days")
    return deleted


def cleanup_job_failures(db: Session, days: int):
    """Delete job failures older than specified days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    deleted = db.query(PreviewJobFailure).filter(
        PreviewJobFailure.created_at < cutoff_date
    ).delete()
    db.commit()
    logger.info(f"Deleted {deleted} job failures older than {days} days")
    return deleted


def main():
    """Run cleanup operations."""
    db = SessionLocal()
    try:
        logger.info("Starting data cleanup...")
        
        variant_count = cleanup_preview_variants(db, PREVIEW_VARIANT_RETENTION_DAYS)
        event_count = cleanup_analytics_events(db, ANALYTICS_EVENT_RETENTION_DAYS)
        failure_count = cleanup_job_failures(db, JOB_FAILURE_RETENTION_DAYS)
        
        logger.info(
            f"Cleanup completed: {variant_count} variants, {event_count} events, {failure_count} failures deleted"
        )
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

