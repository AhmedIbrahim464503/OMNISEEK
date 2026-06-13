from core.celery import celery_app
from core.logging import logger

@celery_app.task(name="workers.worker.ping")
def ping() -> str:
    """Execute simple diagnostic task indicating Celery execution health."""
    logger.info("Celery diagnostic task triggered successfully.")
    return "pong"
