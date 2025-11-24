"""RQ worker for processing background jobs."""
import logging
import time
from rq import Worker, Queue
from rq.job import Job
from backend.queue.queue_connection import get_redis_connection
from backend.utils.logger import setup_logging

# Setup structured logging for worker
setup_logging(level="INFO")
logger = logging.getLogger(__name__)


def create_worker():
    """Create and return RQ worker instance."""
    redis_conn = get_redis_connection()
    queue = Queue("preview_generation", connection=redis_conn)
    worker = Worker([queue], connection=redis_conn)
    return worker


def log_job_start(job: Job):
    """Log job start."""
    logger.info(
        f"Job {job.id} started",
        extra={
            "job_id": job.id,
            "job_name": job.func_name,
            "status": "started",
        }
    )


def log_job_success(job: Job, duration_ms: int):
    """Log job success."""
    logger.info(
        f"Job {job.id} completed successfully",
        extra={
            "job_id": job.id,
            "job_name": job.func_name,
            "status": "success",
            "duration_ms": duration_ms,
        }
    )


def log_job_failure(job: Job, exc: Exception, duration_ms: int):
    """Log job failure."""
    logger.error(
        f"Job {job.id} failed: {str(exc)}",
        extra={
            "job_id": job.id,
            "job_name": job.func_name,
            "status": "failed",
            "duration_ms": duration_ms,
            "error": str(exc),
        },
        exc_info=True
    )


if __name__ == "__main__":
    logger.info("Starting RQ worker for preview generation...")
    worker = create_worker()
    worker.work()

