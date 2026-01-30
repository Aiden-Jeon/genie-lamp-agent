"""Job manager for background task orchestration."""

import asyncio
import uuid
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from typing import Callable, Any

from .session_store import SessionStore, Job


class JobManager:
    """Manages background job execution with process pool."""

    def __init__(self, session_store: SessionStore, max_workers: int = 4):
        """
        Initialize job manager.

        Args:
            session_store: Store for persisting job state
            max_workers: Maximum concurrent jobs
        """
        self.store = session_store
        self.executor = ProcessPoolExecutor(max_workers=max_workers)

    def create_job(self, job_type: str, session_id: str, inputs: dict) -> Job:
        """
        Create a new job record.

        Args:
            job_type: Type of job (parse, generate, validate, deploy)
            session_id: Session identifier
            inputs: Job input parameters

        Returns:
            Created Job object
        """
        job = Job(
            job_id=str(uuid.uuid4()),
            type=job_type,
            session_id=session_id,
            status="pending",
            inputs=inputs,
            created_at=datetime.now()
        )
        self.store.save_job(job)
        return job

    async def run_job(self, job_id: str, task_func: Callable, *args) -> None:
        """
        Execute a job in the background.

        Args:
            job_id: Job identifier
            task_func: Function to execute
            *args: Arguments for task_func
        """
        # Update status to running
        job = self.store.get_job(job_id)
        if not job:
            return

        job.status = "running"
        self.store.update_job(job)

        try:
            # Run in process pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                task_func,
                *args
            )

            # Update with result
            job.status = "completed"
            job.result = result
            job.completed_at = datetime.now()

        except Exception as e:
            # Update with error
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now()

        finally:
            self.store.update_job(job)

    def get_job(self, job_id: str) -> Job:
        """Get job status."""
        return self.store.get_job(job_id)
