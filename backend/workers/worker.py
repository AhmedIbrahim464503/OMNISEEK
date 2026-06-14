import asyncio
import celery
from typing import Any
from core.celery import celery_app
from core.logging import logger
from core.db import AsyncSessionLocal
from services.task_status import TaskStatusService
from services.processing_orchestrator import ProcessingOrchestrator

class DatabaseTrackedTask(celery.Task):
    """Custom Celery Task base class executing lifecycle tracking directly inside PostgreSQL."""

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        task_id = self.request.id
        if task_id:
            logger.info(f"Celery Task {self.name} [{task_id}] is transition to STARTED.")
            TaskStatusService.sync_update(task_id, "STARTED")
        return super().__call__(*args, **kwargs)

    def on_retry(self, exc: Exception, task_id: str, args: Any, kwargs: Any, einfo: Any) -> None:
        logger.warning(f"Celery Task {self.name} [{task_id}] triggered RETRY: {str(exc)}")
        TaskStatusService.sync_update(task_id, "RETRY", error=str(exc))
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval: Any, task_id: str, args: Any, kwargs: Any) -> None:
        logger.info(f"Celery Task {self.name} [{task_id}] executed successfully: SUCCESS.")
        TaskStatusService.sync_update(task_id, "SUCCESS", result={"output": str(retval)})
        super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc: Exception, task_id: str, args: Any, kwargs: Any, einfo: Any) -> None:
        logger.error(f"Celery Task {self.name} [{task_id}] failed: FAILURE. Error: {str(exc)}")
        TaskStatusService.sync_update(task_id, "FAILURE", error=str(exc))
        super().on_failure(exc, task_id, args, kwargs, einfo)

@celery_app.task(name="workers.worker.ping", base=DatabaseTrackedTask, bind=True)
def ping(self) -> str:
    """Diagnostic health check task."""
    logger.info("Diagnostic ping task processed.")
    return "pong"

@celery_app.task(
    name="workers.worker.process_asset_embeddings",
    base=DatabaseTrackedTask,
    bind=True,
    max_retries=3,
    time_limit=600,
    soft_time_limit=540
)
def process_asset_embeddings(self, asset_id: str) -> str:
    """Background embedding generation task executing local AI models with exponential backoff."""
    logger.info(f"Starting Celery background embeddings processing for Asset ID: {asset_id}")
    
    async def _execute():
        async with AsyncSessionLocal() as db:
            orchestrator = ProcessingOrchestrator(db)
            await orchestrator.process_asset_embeddings(asset_id)
            
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    try:
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_execute(), loop)
            future.result()
        else:
            loop.run_until_complete(_execute())
        return f"Successfully processed embeddings for Asset ID: {asset_id}"
    except Exception as exc:
        # Exponential backoff calculations: 10s, 20s, 40s
        countdown = (2 ** self.request.retries) * 10
        logger.error(f"Error processing embeddings for Asset {asset_id}. Retrying in {countdown}s...")
        raise self.retry(exc=exc, countdown=countdown)
