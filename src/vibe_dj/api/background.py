import uuid
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from loguru import logger


class JobStatus:
    """Status information for a background job.

    Tracks job state, progress, timing, and errors.
    """

    def __init__(self, job_id: str):
        """Initialize job status.

        :param job_id: Unique identifier for the job
        """
        self.job_id = job_id
        self.status: Literal["queued", "running", "completed", "failed"] = "queued"
        self.progress: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert job status to dictionary.

        :return: Dictionary representation of job status
        """
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }


class JobManager:
    """In-memory job tracking manager.

    Manages background job status and progress tracking. Uses in-memory
    storage suitable for single-instance deployments.
    """

    def __init__(self):
        """Initialize job manager with empty job store."""
        self._jobs: Dict[str, JobStatus] = {}

    def create_job(self) -> str:
        """Create a new job and return its ID.

        :return: Unique job ID
        """
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = JobStatus(job_id)
        logger.info(f"Created job {job_id}")
        return job_id

    def get_job(self, job_id: str) -> Optional[JobStatus]:
        """Get job status by ID.

        :param job_id: Job identifier
        :return: JobStatus if found, None otherwise
        """
        return self._jobs.get(job_id)

    def start_job(self, job_id: str) -> None:
        """Mark job as running.

        :param job_id: Job identifier
        """
        job = self._jobs.get(job_id)
        if job:
            job.status = "running"
            job.started_at = datetime.now()
            logger.info(f"Job {job_id} started")

    def update_progress(self, job_id: str, progress: Dict[str, Any]) -> None:
        """Update job progress information.

        :param job_id: Job identifier
        :param progress: Progress data dictionary
        """
        job = self._jobs.get(job_id)
        if job:
            job.progress = progress
            logger.debug(f"Job {job_id} progress updated: {progress}")

    def complete_job(self, job_id: str) -> None:
        """Mark job as completed successfully.

        :param job_id: Job identifier
        """
        job = self._jobs.get(job_id)
        if job:
            job.status = "completed"
            job.completed_at = datetime.now()
            logger.info(f"Job {job_id} completed")

    def fail_job(self, job_id: str, error: str) -> None:
        """Mark job as failed with error message.

        :param job_id: Job identifier
        :param error: Error message
        """
        job = self._jobs.get(job_id)
        if job:
            job.status = "failed"
            job.error = error
            job.completed_at = datetime.now()
            logger.error(f"Job {job_id} failed: {error}")

    def get_active_job(self) -> Optional[JobStatus]:
        """Get the currently active (queued or running) job, if any.

        :return: JobStatus if an active job exists, None otherwise
        """
        for job in self._jobs.values():
            if job.status in ("queued", "running"):
                return job
        return None

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remove jobs older than specified age.

        :param max_age_hours: Maximum age in hours to keep jobs
        :return: Number of jobs removed
        """
        now = datetime.now()
        to_remove = []

        for job_id, job in self._jobs.items():
            if job.completed_at:
                age = (now - job.completed_at).total_seconds() / 3600
                if age > max_age_hours:
                    to_remove.append(job_id)

        for job_id in to_remove:
            del self._jobs[job_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")

        return len(to_remove)


job_manager = JobManager()
