from unittest.mock import MagicMock

from vibe_dj.app import app
from vibe_dj.core import MusicDatabase
from vibe_dj.models import Playlist, Song


class TestPlaylistEndpoints:
    """Test playlist generation endpoints."""

    def test_generate_playlist_success(self, client, test_config):
        """Test successful playlist generation."""
        from vibe_dj.api.dependencies import get_playlist_generator

        request_data = {
            "seeds": [
                {
                    "title": "Test Song 1",
                    "artist": "Test Artist 1",
                    "album": "Test Album 1",
                }
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
            "seeds": [{"title": "Nonexistent", "artist": "Unknown", "album": "None"}],
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
