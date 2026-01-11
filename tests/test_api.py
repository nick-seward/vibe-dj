import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from vibe_dj.api.background import JobManager
from vibe_dj.app import app
from vibe_dj.core import MusicDatabase
from vibe_dj.models import Config, Features, Playlist, Song


@pytest.fixture
def test_config():
    """Create a test configuration with in-memory database."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    config = Config(
        database_path=db_path,
        faiss_index_path="test_faiss.bin",
        parallel_workers=2,
    )
    
    yield config
    
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def test_db(test_config):
    """Create a test database with sample data."""
    with MusicDatabase(test_config) as db:
        db.init_db()
        
        song1 = Song(
            id=1,
            file_path="/test/song1.mp3",
            title="Test Song 1",
            artist="Test Artist 1",
            album="Test Album 1",
            genre="Rock",
            last_modified=1234567890.0,
            duration=180,
        )
        song2 = Song(
            id=2,
            file_path="/test/song2.mp3",
            title="Test Song 2",
            artist="Test Artist 2",
            album="Test Album 2",
            genre="Pop",
            last_modified=1234567891.0,
            duration=200,
        )
        
        features1 = Features(
            song_id=1,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0,
        )
        features2 = Features(
            song_id=2,
            feature_vector=np.array([4.0, 5.0, 6.0], dtype=np.float32),
            bpm=130.0,
        )
        
        db.add_song(song1, features1)
        db.add_song(song2, features2)
        
        yield db


@pytest.fixture
def client(test_config):
    """Create a test client with mocked dependencies."""
    from vibe_dj.api.dependencies import get_config
    
    def override_get_config():
        return test_config
    
    app.dependency_overrides[get_config] = override_get_config
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_job_manager():
    """Create a mock job manager."""
    return JobManager()


class TestRootEndpoints:
    """Test root and health check endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API information or UI."""
        response = client.get("/")
        assert response.status_code == 200
        
        # If UI dist exists, root serves HTML; otherwise serves JSON API info
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            data = response.json()
            assert data["name"] == "Vibe-DJ API"
            assert "endpoints" in data
        elif "text/html" in content_type:
            # UI is being served, which is also valid
            assert len(response.content) > 0
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "faiss_index" in data


class TestIndexEndpoints:
    """Test indexing endpoints."""
    
    def test_index_library_success(self, client):
        """Test successful library indexing request."""
        with tempfile.TemporaryDirectory() as tmpdir:
            request_data = {
                "library_path": tmpdir,
                "config_overrides": None,
            }
            
            with patch('vibe_dj.api.routes.index.run_indexing_job'):
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
            
            with patch('vibe_dj.api.routes.index.run_indexing_job'):
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


class TestPlaylistEndpoints:
    """Test playlist generation endpoints."""
    
    def test_generate_playlist_success(self, client, test_config):
        """Test successful playlist generation."""
        from vibe_dj.api.dependencies import get_playlist_generator
        
        request_data = {
            "seeds": [
                {"title": "Test Song 1", "artist": "Test Artist 1", "album": "Test Album 1"}
            ],
            "length": 5,
            "bpm_jitter": 5.0,
            "format": "json",
            "sync_to_navidrome": False,
        }
        
        mock_playlist = Playlist(
            songs=[
                Song(
                    id=1,
                    file_path="/test/song1.mp3",
                    title="Test Song 1",
                    artist="Test Artist 1",
                    album="Test Album 1",
                    genre="Rock",
                    last_modified=1234567890.0,
                    duration=180,
                )
            ],
            seed_songs=[
                Song(
                    id=1,
                    file_path="/test/song1.mp3",
                    title="Test Song 1",
                    artist="Test Artist 1",
                    album="Test Album 1",
                    genre="Rock",
                    last_modified=1234567890.0,
                    duration=180,
                )
            ],
        )
        
        mock_generator = MagicMock()
        mock_generator.generate.return_value = mock_playlist
        
        app.dependency_overrides[get_playlist_generator] = lambda: mock_generator
        
        try:
            response = client.post("/api/playlist", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "songs" in data
            assert "seed_songs" in data
            assert len(data["songs"]) > 0
        finally:
            app.dependency_overrides.pop(get_playlist_generator, None)
    
    def test_generate_playlist_invalid_seeds(self, client):
        """Test playlist generation with invalid seeds."""
        request_data = {
            "seeds": [],
            "length": 5,
        }
        
        response = client.post("/api/playlist", json=request_data)
        
        assert response.status_code == 422
    
    def test_generate_playlist_no_results(self, client):
        """Test playlist generation when no songs found."""
        from vibe_dj.api.dependencies import get_playlist_generator
        
        request_data = {
            "seeds": [
                {"title": "Nonexistent", "artist": "Unknown", "album": "None"}
            ],
            "length": 5,
        }
        
        mock_generator = MagicMock()
        mock_generator.generate.return_value = None
        
        app.dependency_overrides[get_playlist_generator] = lambda: mock_generator
        
        try:
            response = client.post("/api/playlist", json=request_data)
            
            assert response.status_code == 400
        finally:
            app.dependency_overrides.pop(get_playlist_generator, None)
    
    def test_export_playlist_success(self, client, test_config):
        """Test playlist export."""
        from vibe_dj.api.dependencies import get_config, get_playlist_exporter
        
        request_data = {
            "song_ids": [1, 2],
            "format": "m3u",
            "output_path": "/tmp/test_playlist.m3u",
        }
        
        mock_song1 = Song(
            id=1,
            file_path="/test/song1.mp3",
            title="Test Song 1",
            artist="Test Artist 1",
            album="Test Album 1",
            genre="Rock",
            last_modified=1234567890.0,
            duration=180,
        )
        mock_song2 = Song(
            id=2,
            file_path="/test/song2.mp3",
            title="Test Song 2",
            artist="Test Artist 2",
            album="Test Album 2",
            genre="Pop",
            last_modified=1234567891.0,
            duration=200,
        )
        
        # Create a real database with test data
        with MusicDatabase(test_config) as db:
            db.init_db()
            db.add_song(mock_song1)
            db.add_song(mock_song2)
        
        mock_exporter = MagicMock()
        
        app.dependency_overrides[get_config] = lambda: test_config
        app.dependency_overrides[get_playlist_exporter] = lambda: mock_exporter
        
        try:
            response = client.post("/api/export", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["song_count"] == 2
        finally:
            app.dependency_overrides.pop(get_config, None)
            app.dependency_overrides.pop(get_playlist_exporter, None)
    
    def test_export_playlist_song_not_found(self, client, test_config):
        """Test export with non-existent song ID."""
        from vibe_dj.api.dependencies import get_config
        
        request_data = {
            "song_ids": [999],
            "format": "m3u",
            "output_path": "/tmp/test_playlist.m3u",
        }
        
        # Create empty database
        with MusicDatabase(test_config) as db:
            db.init_db()
        
        app.dependency_overrides[get_config] = lambda: test_config
        
        try:
            response = client.post("/api/export", json=request_data)
            
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_config, None)


class TestSongsEndpoints:
    """Test song listing and retrieval endpoints."""
    
    def test_list_songs_default(self, client):
        """Test listing songs with default pagination."""
        from vibe_dj.api.dependencies import get_db
        
        mock_songs = [
            Song(
                id=1,
                file_path="/test/song1.mp3",
                title="Test Song 1",
                artist="Test Artist 1",
                album="Test Album 1",
                genre="Rock",
                last_modified=1234567890.0,
                duration=180,
            ),
            Song(
                id=2,
                file_path="/test/song2.mp3",
                title="Test Song 2",
                artist="Test Artist 2",
                album="Test Album 2",
                genre="Pop",
                last_modified=1234567891.0,
                duration=200,
            ),
        ]
        
        mock_db = MagicMock()
        mock_db.get_all_songs.return_value = mock_songs
        mock_db.count_songs.return_value = 2
        
        def override_get_db():
            yield mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            response = client.get("/api/songs")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert len(data["songs"]) == 2
            assert data["limit"] == 100
            assert data["offset"] == 0
        finally:
            app.dependency_overrides.pop(get_db, None)
    
    def test_list_songs_with_pagination(self, client):
        """Test listing songs with custom pagination."""
        from vibe_dj.api.dependencies import get_db
        
        mock_db = MagicMock()
        mock_db.get_all_songs.return_value = []
        mock_db.count_songs.return_value = 100
        
        def override_get_db():
            yield mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            response = client.get("/api/songs?limit=10&offset=20")
            
            assert response.status_code == 200
            data = response.json()
            assert data["limit"] == 10
            assert data["offset"] == 20
        finally:
            app.dependency_overrides.pop(get_db, None)
    
    def test_list_songs_with_search(self, client):
        """Test listing songs with search query."""
        from vibe_dj.api.dependencies import get_db
        
        mock_songs = [
            Song(
                id=1,
                file_path="/test/song1.mp3",
                title="Rock Song",
                artist="Rock Artist",
                album="Rock Album",
                genre="Rock",
                last_modified=1234567890.0,
                duration=180,
            ),
        ]
        
        mock_db = MagicMock()
        mock_db.search_songs.return_value = mock_songs
        mock_db.count_songs.return_value = 1
        
        def override_get_db():
            yield mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            response = client.get("/api/songs?search=Rock")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["songs"]) == 1
        finally:
            app.dependency_overrides.pop(get_db, None)
    
    def test_get_song_by_id_success(self, client):
        """Test getting a specific song by ID."""
        from vibe_dj.api.dependencies import get_db
        
        mock_song = Song(
            id=1,
            file_path="/test/song1.mp3",
            title="Test Song 1",
            artist="Test Artist 1",
            album="Test Album 1",
            genre="Rock",
            last_modified=1234567890.0,
            duration=180,
        )
        mock_features = Features(
            song_id=1,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0,
        )
        
        mock_db = MagicMock()
        mock_db.get_song.return_value = mock_song
        mock_db.get_features.return_value = mock_features
        
        def override_get_db():
            yield mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            response = client.get("/api/songs/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["song"]["id"] == 1
            assert data["song"]["title"] == "Test Song 1"
            assert data["features"] is not None
            assert data["features"]["bpm"] == 120.0
        finally:
            app.dependency_overrides.pop(get_db, None)
    
    def test_get_song_by_id_not_found(self, client):
        """Test getting a non-existent song."""
        from vibe_dj.api.dependencies import get_db
        
        mock_db = MagicMock()
        mock_db.get_song.return_value = None
        
        def override_get_db():
            yield mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            response = client.get("/api/songs/999")
            
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_db, None)
    
    def test_get_song_without_features(self, client):
        """Test getting a song without features."""
        from vibe_dj.api.dependencies import get_db
        
        mock_song = Song(
            id=1,
            file_path="/test/song1.mp3",
            title="Test Song 1",
            artist="Test Artist 1",
            album="Test Album 1",
            genre="Rock",
            last_modified=1234567890.0,
            duration=180,
        )
        
        mock_db = MagicMock()
        mock_db.get_song.return_value = mock_song
        mock_db.get_features.return_value = None
        
        def override_get_db():
            yield mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            response = client.get("/api/songs/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["song"]["id"] == 1
            assert data["features"] is None
        finally:
            app.dependency_overrides.pop(get_db, None)


class TestSearchSongsMultiEndpoint:
    """Test the /songs/search endpoint with pagination."""
    
    def test_search_songs_multi_default_pagination(self, client):
        """Test search with default pagination (50 results per page)."""
        from vibe_dj.api.dependencies import get_db
        
        mock_songs = [
            Song(
                id=i,
                file_path=f"/test/song{i}.mp3",
                title=f"Test Song {i}",
                artist="Test Artist",
                album="Test Album",
                genre="Rock",
                last_modified=1234567890.0,
                duration=180,
            )
            for i in range(50)
        ]
        
        mock_db = MagicMock()
        mock_db.search_songs_multi.return_value = mock_songs
        mock_db.count_songs_multi.return_value = 100
        
        def override_get_db():
            yield mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            response = client.get("/api/songs/search?artist=Test")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 100
            assert len(data["songs"]) == 50
            assert data["limit"] == 50
            assert data["offset"] == 0
        finally:
            app.dependency_overrides.pop(get_db, None)
    
    def test_search_songs_multi_with_pagination(self, client):
        """Test search with custom pagination parameters."""
        from vibe_dj.api.dependencies import get_db
        
        mock_songs = [
            Song(
                id=i,
                file_path=f"/test/song{i}.mp3",
                title=f"Test Song {i}",
                artist="Test Artist",
                album="Test Album",
                genre="Rock",
                last_modified=1234567890.0,
                duration=180,
            )
            for i in range(100)
        ]
        
        mock_db = MagicMock()
        mock_db.search_songs_multi.return_value = mock_songs
        mock_db.count_songs_multi.return_value = 500
        
        def override_get_db():
            yield mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            response = client.get("/api/songs/search?artist=Test&limit=100&offset=50")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 500
            assert data["limit"] == 100
            assert data["offset"] == 50
        finally:
            app.dependency_overrides.pop(get_db, None)
    
    def test_search_songs_multi_max_limit(self, client):
        """Test that limit is capped at 200."""
        response = client.get("/api/songs/search?artist=Test&limit=300")
        
        assert response.status_code == 422  # Validation error
    
    def test_search_songs_multi_max_depth_exceeded(self, client):
        """Test that offset + limit cannot exceed 1000."""
        from vibe_dj.api.dependencies import get_db
        
        mock_db = MagicMock()
        mock_db.search_songs_multi.return_value = []
        mock_db.count_songs_multi.return_value = 2000
        
        def override_get_db():
            yield mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            response = client.get("/api/songs/search?artist=Test&limit=200&offset=900")
            
            assert response.status_code == 400
            data = response.json()
            error_msg = data.get("detail") or data.get("error", "")
            assert "1000" in error_msg
        finally:
            app.dependency_overrides.pop(get_db, None)
    
    def test_search_songs_multi_at_max_depth(self, client):
        """Test that offset + limit at exactly 1000 is allowed."""
        from vibe_dj.api.dependencies import get_db
        
        mock_songs = [
            Song(
                id=i,
                file_path=f"/test/song{i}.mp3",
                title=f"Test Song {i}",
                artist="Test Artist",
                album="Test Album",
                genre="Rock",
                last_modified=1234567890.0,
                duration=180,
            )
            for i in range(200)
        ]
        
        mock_db = MagicMock()
        mock_db.search_songs_multi.return_value = mock_songs
        mock_db.count_songs_multi.return_value = 2000
        
        def override_get_db():
            yield mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            response = client.get("/api/songs/search?artist=Test&limit=200&offset=800")
            
            assert response.status_code == 200
            data = response.json()
            assert data["limit"] == 200
            assert data["offset"] == 800
        finally:
            app.dependency_overrides.pop(get_db, None)
    
    def test_search_songs_multi_requires_at_least_one_param(self, client):
        """Test that at least one search parameter is required."""
        response = client.get("/api/songs/search")
        
        assert response.status_code == 400
        data = response.json()
        error_msg = data.get("detail") or data.get("error", "")
        assert "at least one search parameter" in error_msg.lower()
    
    def test_search_songs_multi_page_size_options(self, client):
        """Test all valid page size options (50, 100, 150, 200)."""
        from vibe_dj.api.dependencies import get_db
        
        mock_db = MagicMock()
        mock_db.search_songs_multi.return_value = []
        mock_db.count_songs_multi.return_value = 0
        
        def override_get_db():
            yield mock_db
        
        app.dependency_overrides[get_db] = override_get_db
        
        try:
            for page_size in [50, 100, 150, 200]:
                response = client.get(f"/api/songs/search?artist=Test&limit={page_size}")
                assert response.status_code == 200
                data = response.json()
                assert data["limit"] == page_size
        finally:
            app.dependency_overrides.pop(get_db, None)


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
