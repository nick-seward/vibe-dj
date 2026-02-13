import tempfile
from unittest.mock import MagicMock, patch

from vibe_dj.api.background import JobManager
from vibe_dj.app import app


class TestIndexEndpoints:
    """Test indexing endpoints."""

    def test_index_library_success(self, client):
        """Test successful library indexing request."""
        with tempfile.TemporaryDirectory() as tmpdir:
            request_data = {
                "library_path": tmpdir,
                "config_overrides": None,
            }

            with patch("vibe_dj.api.routes.index.run_indexing_job"):
                response = client.post("/api/index", json=request_data)

                assert response.status_code == 200
                data = response.json()
                assert "job_id" in data
                assert data["status"] == "queued"
                assert tmpdir in data["message"]

    def test_index_library_with_config_overrides(self, client):
        """Test indexing with configuration overrides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            request_data = {
                "library_path": tmpdir,
                "config_overrides": {
                    "parallel_workers": 8,
                    "batch_size": 20,
                },
            }

            with patch("vibe_dj.api.routes.index.run_indexing_job"):
                response = client.post("/api/index", json=request_data)

                assert response.status_code == 200
                data = response.json()
                assert "job_id" in data

    def test_get_job_status_success(self, client):
        """Test getting job status for existing job."""
        from vibe_dj.api.dependencies import get_job_manager

        mock_manager = MagicMock()
        mock_job = MagicMock()
        mock_job.job_id = "test-job-123"
        mock_job.status = "running"
        mock_job.progress = {"phase": "scanning"}
        mock_job.error = None
        mock_job.started_at = None
        mock_job.completed_at = None

        mock_manager.get_job.return_value = mock_job

        app.dependency_overrides[get_job_manager] = lambda: mock_manager

        try:
            response = client.get("/api/status/test-job-123")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "test-job-123"
            assert data["status"] == "running"
        finally:
            app.dependency_overrides.pop(get_job_manager, None)

    def test_get_job_status_not_found(self, client):
        """Test getting status for non-existent job."""
        from vibe_dj.api.dependencies import get_job_manager

        mock_manager = MagicMock()
        mock_manager.get_job.return_value = None

        app.dependency_overrides[get_job_manager] = lambda: mock_manager

        try:
            response = client.get("/api/status/nonexistent-job")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_job_manager, None)


class TestActiveJobEndpoint:
    """Test GET /api/index/active endpoint."""

    def test_no_active_job_returns_idle(self, client):
        """Test that idle response is returned when no job is active."""
        from vibe_dj.api.dependencies import get_job_manager

        mock_manager = MagicMock()
        mock_manager.get_active_job.return_value = None

        app.dependency_overrides[get_job_manager] = lambda: mock_manager

        try:
            response = client.get("/api/index/active")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] is None
            assert data["status"] == "idle"
            assert data["progress"] is None
        finally:
            app.dependency_overrides.pop(get_job_manager, None)

    def test_active_running_job(self, client):
        """Test that running job status is returned when a job is active."""
        from vibe_dj.api.dependencies import get_job_manager

        mock_job = MagicMock()
        mock_job.job_id = "active-job-123"
        mock_job.status = "running"
        mock_job.progress = {"phase": "metadata", "processed": 5, "total": 10}
        mock_job.error = None
        mock_job.started_at = None
        mock_job.completed_at = None

        mock_manager = MagicMock()
        mock_manager.get_active_job.return_value = mock_job

        app.dependency_overrides[get_job_manager] = lambda: mock_manager

        try:
            response = client.get("/api/index/active")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "active-job-123"
            assert data["status"] == "running"
            assert data["progress"]["phase"] == "metadata"
            assert data["progress"]["processed"] == 5
        finally:
            app.dependency_overrides.pop(get_job_manager, None)

    def test_active_queued_job(self, client):
        """Test that queued job status is returned when a job is queued."""
        from vibe_dj.api.dependencies import get_job_manager

        mock_job = MagicMock()
        mock_job.job_id = "queued-job-456"
        mock_job.status = "queued"
        mock_job.progress = None
        mock_job.error = None
        mock_job.started_at = None
        mock_job.completed_at = None

        mock_manager = MagicMock()
        mock_manager.get_active_job.return_value = mock_job

        app.dependency_overrides[get_job_manager] = lambda: mock_manager

        try:
            response = client.get("/api/index/active")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "queued-job-456"
            assert data["status"] == "queued"
        finally:
            app.dependency_overrides.pop(get_job_manager, None)


class TestRunIndexingJob:
    """Test the run_indexing_job background function directly."""

    def test_progress_callback_wired_to_job_manager(self, test_config):
        """Test that run_indexing_job passes a progress callback that calls update_progress."""
        from vibe_dj.api.routes.index import run_indexing_job

        job_manager = JobManager()
        job_id = job_manager.create_job()

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("vibe_dj.api.routes.index.MusicDatabase") as mock_db_cls,
                patch("vibe_dj.api.routes.index.AudioAnalyzer"),
                patch("vibe_dj.api.routes.index.SimilarityIndex"),
                patch("vibe_dj.api.routes.index.LibraryIndexer") as mock_indexer_cls,
            ):
                mock_db = MagicMock()
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=False)
                mock_db_cls.return_value = mock_db

                # Capture the progress_callback passed to index_library
                captured_callback = {}

                def fake_index_library(path, progress_callback=None):
                    captured_callback["cb"] = progress_callback
                    if progress_callback:
                        progress_callback("metadata", 5, 10)
                        progress_callback("features", 3, 10)

                mock_indexer = MagicMock()
                mock_indexer.index_library.side_effect = fake_index_library
                mock_indexer_cls.return_value = mock_indexer

                run_indexing_job(job_id, tmpdir, test_config, job_manager)

                # Verify a callback was passed
                assert "cb" in captured_callback
                assert captured_callback["cb"] is not None

                # Verify job completed
                job = job_manager.get_job(job_id)
                assert job.status == "completed"

                # Verify progress was updated with structured data
                # The last progress update should be the "completed" phase
                assert job.progress["phase"] == "completed"

    def test_progress_callback_sends_structured_data(self, test_config):
        """Test that progress callback sends phase, processed, total, and message."""
        from vibe_dj.api.routes.index import run_indexing_job

        mock_job_manager = MagicMock(spec=JobManager)

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                patch("vibe_dj.api.routes.index.MusicDatabase") as mock_db_cls,
                patch("vibe_dj.api.routes.index.AudioAnalyzer"),
                patch("vibe_dj.api.routes.index.SimilarityIndex"),
                patch("vibe_dj.api.routes.index.LibraryIndexer") as mock_indexer_cls,
            ):
                mock_db = MagicMock()
                mock_db.__enter__ = MagicMock(return_value=mock_db)
                mock_db.__exit__ = MagicMock(return_value=False)
                mock_db_cls.return_value = mock_db

                def fake_index_library(path, progress_callback=None):
                    if progress_callback:
                        progress_callback("metadata", 2, 5)
                        progress_callback("features", 1, 5)

                mock_indexer = MagicMock()
                mock_indexer.index_library.side_effect = fake_index_library
                mock_indexer_cls.return_value = mock_indexer

                run_indexing_job("test-job", tmpdir, test_config, mock_job_manager)

                # Collect all update_progress calls
                progress_calls = mock_job_manager.update_progress.call_args_list

                # Should have: scanning, metadata, features, completed
                assert len(progress_calls) >= 4

                # Check scanning phase
                scanning_data = progress_calls[0][0][1]
                assert scanning_data["phase"] == "scanning"

                # Check metadata callback
                metadata_data = progress_calls[1][0][1]
                assert metadata_data["phase"] == "metadata"
                assert metadata_data["processed"] == 2
                assert metadata_data["total"] == 5
                assert "Extracting metadata (2/5)" == metadata_data["message"]

                # Check features callback
                features_data = progress_calls[2][0][1]
                assert features_data["phase"] == "features"
                assert features_data["processed"] == 1
                assert features_data["total"] == 5
                assert "Analyzing audio (1/5)" == features_data["message"]

                # Check completed phase
                completed_data = progress_calls[3][0][1]
                assert completed_data["phase"] == "completed"
