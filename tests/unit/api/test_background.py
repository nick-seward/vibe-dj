from vibe_dj.api.background import JobManager


class TestBackgroundJobManager:
    """Test background job manager functionality."""

    def test_create_job(self):
        """Test job creation."""
        manager = JobManager()
        job_id = manager.create_job()

        assert job_id is not None
        assert len(job_id) > 0

        job = manager.get_job(job_id)
        assert job is not None
        assert job.status == "queued"

    def test_start_job(self):
        """Test starting a job."""
        manager = JobManager()
        job_id = manager.create_job()

        manager.start_job(job_id)
        job = manager.get_job(job_id)

        assert job.status == "running"
        assert job.started_at is not None

    def test_update_progress(self):
        """Test updating job progress."""
        manager = JobManager()
        job_id = manager.create_job()

        progress = {"phase": "scanning", "files_processed": 10}
        manager.update_progress(job_id, progress)

        job = manager.get_job(job_id)
        assert job.progress == progress

    def test_complete_job(self):
        """Test completing a job."""
        manager = JobManager()
        job_id = manager.create_job()
        manager.start_job(job_id)

        manager.complete_job(job_id)
        job = manager.get_job(job_id)

        assert job.status == "completed"
        assert job.completed_at is not None

    def test_fail_job(self):
        """Test failing a job."""
        manager = JobManager()
        job_id = manager.create_job()
        manager.start_job(job_id)

        error_msg = "Test error"
        manager.fail_job(job_id, error_msg)

        job = manager.get_job(job_id)
        assert job.status == "failed"
        assert job.error == error_msg
        assert job.completed_at is not None

    def test_get_nonexistent_job(self):
        """Test getting a non-existent job."""
        manager = JobManager()
        job = manager.get_job("nonexistent-id")

        assert job is None

    def test_get_active_job_no_jobs(self):
        """Test get_active_job returns None when no jobs exist."""
        manager = JobManager()

        assert manager.get_active_job() is None

    def test_get_active_job_queued(self):
        """Test get_active_job returns a queued job."""
        manager = JobManager()
        job_id = manager.create_job()

        active = manager.get_active_job()
        assert active is not None
        assert active.job_id == job_id
        assert active.status == "queued"

    def test_get_active_job_running(self):
        """Test get_active_job returns a running job."""
        manager = JobManager()
        job_id = manager.create_job()
        manager.start_job(job_id)

        active = manager.get_active_job()
        assert active is not None
        assert active.job_id == job_id
        assert active.status == "running"

    def test_get_active_job_all_completed(self):
        """Test get_active_job returns None when all jobs are completed."""
        manager = JobManager()
        job_id = manager.create_job()
        manager.start_job(job_id)
        manager.complete_job(job_id)

        assert manager.get_active_job() is None

    def test_get_active_job_all_failed(self):
        """Test get_active_job returns None when all jobs are failed."""
        manager = JobManager()
        job_id = manager.create_job()
        manager.start_job(job_id)
        manager.fail_job(job_id, "error")

        assert manager.get_active_job() is None
