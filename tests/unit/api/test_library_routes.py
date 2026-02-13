from unittest.mock import MagicMock

from vibe_dj.app import app


class TestLibraryStatsEndpoint:
    """Test the /api/library/stats endpoint."""

    def test_get_library_stats_success(self, client):
        """Test getting library stats with data."""
        from vibe_dj.api.dependencies import get_db

        mock_db = MagicMock()
        mock_db.get_library_stats.return_value = {
            "total_songs": 500,
            "artist_count": 50,
            "album_count": 80,
            "total_duration": 108000,
            "songs_with_features": 450,
            "last_indexed": 1707782400.0,
        }

        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.get("/api/library/stats")

            assert response.status_code == 200
            data = response.json()
            assert data["total_songs"] == 500
            assert data["artist_count"] == 50
            assert data["album_count"] == 80
            assert data["total_duration"] == 108000
            assert data["songs_with_features"] == 450
            assert data["last_indexed"] == 1707782400.0
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_get_library_stats_empty(self, client):
        """Test getting library stats with no data."""
        from vibe_dj.api.dependencies import get_db

        mock_db = MagicMock()
        mock_db.get_library_stats.return_value = {
            "total_songs": 0,
            "artist_count": 0,
            "album_count": 0,
            "total_duration": 0,
            "songs_with_features": 0,
            "last_indexed": None,
        }

        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.get("/api/library/stats")

            assert response.status_code == 200
            data = response.json()
            assert data["total_songs"] == 0
            assert data["artist_count"] == 0
            assert data["album_count"] == 0
            assert data["total_duration"] == 0
            assert data["songs_with_features"] == 0
            assert data["last_indexed"] is None
        finally:
            app.dependency_overrides.pop(get_db, None)

    def test_get_library_stats_db_error(self, client):
        """Test getting library stats when database fails."""
        from vibe_dj.api.dependencies import get_db

        mock_db = MagicMock()
        mock_db.get_library_stats.side_effect = RuntimeError("Database error")

        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.get("/api/library/stats")

            assert response.status_code == 500
        finally:
            app.dependency_overrides.pop(get_db, None)
