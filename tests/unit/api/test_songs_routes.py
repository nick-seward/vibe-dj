from unittest.mock import MagicMock

import numpy as np

from vibe_dj.app import app
from vibe_dj.models import Features, Song


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
                response = client.get(
                    f"/api/songs/search?artist=Test&limit={page_size}"
                )
                assert response.status_code == 200
                data = response.json()
                assert data["limit"] == page_size
        finally:
            app.dependency_overrides.pop(get_db, None)
