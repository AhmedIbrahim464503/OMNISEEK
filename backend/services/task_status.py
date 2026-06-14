import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.db import AsyncSessionLocal
from models.task_status import TaskStatus

class TaskStatusService:
    """Service layer tracking and managing Celery task lifecycle states in the database."""

    @staticmethod
    async def create_task_status(db: AsyncSession, task_id: str, task_name: str) -> TaskStatus:
        """Create a new TaskStatus entry with PENDING state."""
        task = TaskStatus(id=task_id, task_name=task_name, status="PENDING")
        db.add(task)
        await db.commit()
        return task

    @staticmethod
    async def update_task_status(
        db: AsyncSession,
        task_id: str,
        status: str,
        result: Optional[dict] = None,
        error: Optional[str] = None
    ) -> Optional[TaskStatus]:
        """Update status and capture results/errors for a task."""
        stmt = select(TaskStatus).filter(TaskStatus.id == task_id)
        res = await db.execute(stmt)
        task = res.scalar_one_or_none()
        if task:
            task.status = status
            if result is not None:
                task.result = result
            if error is not None:
                task.error = error
            await db.commit()
        return task

    @classmethod
    def sync_update(cls, task_id: str, status: str, result: Optional[dict] = None, error: Optional[str] = None) -> None:
        """Synchronous wrapper enabling Celery workers to write status updates to the database."""
        async def _run():
            async with AsyncSessionLocal() as db:
                await cls.update_task_status(db, task_id, status, result, error)
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_run(), loop)
            future.result()
        else:
            loop.run_until_complete(_run())

    @classmethod
    def sync_create(cls, task_id: str, task_name: str) -> None:
        """Synchronous wrapper enabling Celery workers to register new tasks in the database."""
        async def _run():
            async with AsyncSessionLocal() as db:
                await cls.create_task_status(db, task_id, task_name)
                
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_run(), loop)
            future.result()
        else:
            loop.run_until_complete(_run())
