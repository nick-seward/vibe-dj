from unittest.mock import MagicMock, patch

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

    def test_generate_playlist_sync_to_navidrome_in_memory_no_tempfile(self, client):
        """Test sync path does not require temporary playlist files."""
        from vibe_dj.api.dependencies import (
            get_navidrome_sync_service,
            get_playlist_generator,
        )

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
            "sync_to_navidrome": True,
            "navidrome_config": {
                "playlist_name": "API Playlist",
                "url": "http://navidrome:4533",
                "username": "api_user",
                "password": "api_pass",
            },
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

        mock_sync_service = MagicMock()
        mock_sync_service.sync_playlist.return_value = {"success": True}

        app.dependency_overrides[get_playlist_generator] = lambda: mock_generator
        app.dependency_overrides[get_navidrome_sync_service] = lambda: mock_sync_service

        try:
            with patch(
                "tempfile.NamedTemporaryFile",
                side_effect=AssertionError("Temporary files should not be used for sync"),
            ):
                response = client.post("/api/playlist", json=request_data)

            assert response.status_code == 200

            mock_sync_service.sync_playlist.assert_called_once()
            args = mock_sync_service.sync_playlist.call_args.args
            assert args[0] is mock_playlist
            assert args[1:] == (
                "API Playlist",
                "http://navidrome:4533",
                "api_user",
                "api_pass",
            )
        finally:
            app.dependency_overrides.pop(get_playlist_generator, None)
            app.dependency_overrides.pop(get_navidrome_sync_service, None)

    def test_sync_playlist_to_navidrome_contract(self, client, test_config):
        """Test /api/playlist/sync passes in-memory playlist data to sync service."""
        from vibe_dj.api.dependencies import get_config, get_navidrome_sync_service

        request_data = {
            "song_ids": [1, 2],
            "navidrome_config": {
                "playlist_name": "Synced Playlist",
                "url": "http://navidrome:4533",
                "username": "sync_user",
                "password": "sync_pass",
            },
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

        with MusicDatabase(test_config) as db:
            db.init_db()
            db.add_song(mock_song1)
            db.add_song(mock_song2)

        mock_sync_service = MagicMock()
        mock_sync_service.sync_playlist.return_value = {
            "success": True,
            "playlist_name": "Synced Playlist",
            "playlist_id": "playlist_123",
            "matched_count": 2,
            "total_count": 2,
            "action": "created",
        }

        app.dependency_overrides[get_config] = lambda: test_config
        app.dependency_overrides[get_navidrome_sync_service] = lambda: mock_sync_service

        try:
            response = client.post("/api/playlist/sync", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["playlist_name"] == "Synced Playlist"
            assert data["playlist_id"] == "playlist_123"
            assert data["matched_count"] == 2
            assert data["total_count"] == 2
            assert data["action"] == "created"

            mock_sync_service.sync_playlist.assert_called_once()
            args = mock_sync_service.sync_playlist.call_args.args
            assert len(args[0].songs) == 2
            assert args[1:] == (
                "Synced Playlist",
                "http://navidrome:4533",
                "sync_user",
                "sync_pass",
            )
        finally:
            app.dependency_overrides.pop(get_config, None)
            app.dependency_overrides.pop(get_navidrome_sync_service, None)

