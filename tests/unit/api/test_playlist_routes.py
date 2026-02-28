from unittest.mock import MagicMock, patch

from vibe_dj.app import app
from vibe_dj.core import MusicDatabase
from vibe_dj.models import Playlist, Song


def _make_mock_profile(url=None, username=None, password=None):
    """Create a mock Profile object."""
    profile = MagicMock()
    profile.subsonic_url = url
    profile.subsonic_username = username
    profile.subsonic_password_encrypted = password
    return profile


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
                side_effect=AssertionError(
                    "Temporary files should not be used for sync"
                ),
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


class TestPlaylistProfileCredentials:
    """Test credential resolution order for playlist endpoints."""

    def _make_song(self, song_id=1):
        return Song(
            id=song_id,
            file_path=f"/test/song{song_id}.mp3",
            title=f"Test Song {song_id}",
            artist=f"Test Artist {song_id}",
            album=f"Test Album {song_id}",
            genre="Rock",
            last_modified=1234567890.0,
            duration=180,
        )

    def test_generate_playlist_uses_profile_credentials_when_no_nav_config(
        self, client
    ):
        """Test that profile credentials are used when no navidrome_config in request."""
        from vibe_dj.api.dependencies import (
            get_active_profile,
            get_navidrome_sync_service,
            get_playlist_generator,
            get_profile_database,
        )

        mock_playlist = Playlist(
            songs=[self._make_song()],
            seed_songs=[self._make_song()],
        )
        mock_generator = MagicMock()
        mock_generator.generate.return_value = mock_playlist

        mock_sync_service = MagicMock()
        mock_sync_service.sync_playlist.return_value = {"success": True}

        mock_profile = _make_mock_profile(
            url="http://8.8.8.8:4533",
            username="profile_user",
            password="profile_pass",
        )
        mock_profile_db = MagicMock()
        mock_profile_db.decrypt_password.side_effect = lambda p: p

        app.dependency_overrides[get_playlist_generator] = lambda: mock_generator
        app.dependency_overrides[get_navidrome_sync_service] = lambda: mock_sync_service
        app.dependency_overrides[get_active_profile] = lambda: mock_profile
        app.dependency_overrides[get_profile_database] = lambda: mock_profile_db

        try:
            response = client.post(
                "/api/playlist",
                json={
                    "seeds": [{"title": "T", "artist": "A", "album": "B"}],
                    "length": 5,
                    "sync_to_navidrome": True,
                },
            )

            assert response.status_code == 200
            mock_sync_service.sync_playlist.assert_called_once()
            _, _, url, username, password = (
                mock_sync_service.sync_playlist.call_args.args
            )
            assert url == "http://8.8.8.8:4533"
            assert username == "profile_user"
            assert password == "profile_pass"
        finally:
            app.dependency_overrides.pop(get_playlist_generator, None)
            app.dependency_overrides.pop(get_navidrome_sync_service, None)
            app.dependency_overrides.pop(get_active_profile, None)
            app.dependency_overrides.pop(get_profile_database, None)

    def test_generate_playlist_request_params_override_profile(self, client):
        """Test that explicit navidrome_config params override profile credentials."""
        from vibe_dj.api.dependencies import (
            get_active_profile,
            get_navidrome_sync_service,
            get_playlist_generator,
            get_profile_database,
        )

        mock_playlist = Playlist(
            songs=[self._make_song()],
            seed_songs=[self._make_song()],
        )
        mock_generator = MagicMock()
        mock_generator.generate.return_value = mock_playlist

        mock_sync_service = MagicMock()
        mock_sync_service.sync_playlist.return_value = {"success": True}

        mock_profile = _make_mock_profile(
            url="http://profile.url:4533",
            username="profile_user",
            password="profile_pass",
        )
        mock_profile_db = MagicMock()
        mock_profile_db.decrypt_password.side_effect = lambda p: p

        app.dependency_overrides[get_playlist_generator] = lambda: mock_generator
        app.dependency_overrides[get_navidrome_sync_service] = lambda: mock_sync_service
        app.dependency_overrides[get_active_profile] = lambda: mock_profile
        app.dependency_overrides[get_profile_database] = lambda: mock_profile_db

        try:
            response = client.post(
                "/api/playlist",
                json={
                    "seeds": [{"title": "T", "artist": "A", "album": "B"}],
                    "length": 5,
                    "sync_to_navidrome": True,
                    "navidrome_config": {
                        "url": "http://8.8.8.8:4533",
                        "username": "request_user",
                        "password": "request_pass",
                    },
                },
            )

            assert response.status_code == 200
            mock_sync_service.sync_playlist.assert_called_once()
            _, _, url, username, password = (
                mock_sync_service.sync_playlist.call_args.args
            )
            assert url == "http://8.8.8.8:4533"
            assert username == "request_user"
            assert password == "request_pass"
        finally:
            app.dependency_overrides.pop(get_playlist_generator, None)
            app.dependency_overrides.pop(get_navidrome_sync_service, None)
            app.dependency_overrides.pop(get_active_profile, None)
            app.dependency_overrides.pop(get_profile_database, None)

    def test_sync_playlist_uses_profile_credentials_when_no_nav_config(
        self, client, test_config
    ):
        """Test /api/playlist/sync uses profile credentials when no nav_config provided."""
        from vibe_dj.api.dependencies import (
            get_active_profile,
            get_config,
            get_navidrome_sync_service,
            get_profile_database,
        )

        song = self._make_song(1)
        with MusicDatabase(test_config) as db:
            db.init_db()
            db.add_song(song)

        mock_sync_service = MagicMock()
        mock_sync_service.sync_playlist.return_value = {
            "success": True,
            "playlist_name": "Vibe DJ Playlist",
            "playlist_id": "pl_1",
            "matched_count": 1,
            "total_count": 1,
            "action": "created",
        }

        mock_profile = _make_mock_profile(
            url="http://8.8.8.8:4533",
            username="profile_user",
            password="profile_pass",
        )
        mock_profile_db = MagicMock()
        mock_profile_db.decrypt_password.side_effect = lambda p: p

        app.dependency_overrides[get_config] = lambda: test_config
        app.dependency_overrides[get_navidrome_sync_service] = lambda: mock_sync_service
        app.dependency_overrides[get_active_profile] = lambda: mock_profile
        app.dependency_overrides[get_profile_database] = lambda: mock_profile_db

        try:
            response = client.post(
                "/api/playlist/sync",
                json={"song_ids": [1]},
            )

            assert response.status_code == 200
            mock_sync_service.sync_playlist.assert_called_once()
            _, _, url, username, password = (
                mock_sync_service.sync_playlist.call_args.args
            )
            assert url == "http://8.8.8.8:4533"
            assert username == "profile_user"
            assert password == "profile_pass"
        finally:
            app.dependency_overrides.pop(get_config, None)
            app.dependency_overrides.pop(get_navidrome_sync_service, None)
            app.dependency_overrides.pop(get_active_profile, None)
            app.dependency_overrides.pop(get_profile_database, None)

    def test_sync_playlist_request_params_override_profile(self, client, test_config):
        """Test /api/playlist/sync request params override profile credentials."""
        from vibe_dj.api.dependencies import (
            get_active_profile,
            get_config,
            get_navidrome_sync_service,
            get_profile_database,
        )

        song = self._make_song(1)
        with MusicDatabase(test_config) as db:
            db.init_db()
            db.add_song(song)

        mock_sync_service = MagicMock()
        mock_sync_service.sync_playlist.return_value = {
            "success": True,
            "playlist_name": "My Playlist",
            "playlist_id": "pl_1",
            "matched_count": 1,
            "total_count": 1,
            "action": "created",
        }

        mock_profile = _make_mock_profile(
            url="http://profile.url:4533",
            username="profile_user",
            password="profile_pass",
        )
        mock_profile_db = MagicMock()
        mock_profile_db.decrypt_password.side_effect = lambda p: p

        app.dependency_overrides[get_config] = lambda: test_config
        app.dependency_overrides[get_navidrome_sync_service] = lambda: mock_sync_service
        app.dependency_overrides[get_active_profile] = lambda: mock_profile
        app.dependency_overrides[get_profile_database] = lambda: mock_profile_db

        try:
            response = client.post(
                "/api/playlist/sync",
                json={
                    "song_ids": [1],
                    "navidrome_config": {
                        "url": "http://8.8.8.8:4533",
                        "username": "request_user",
                        "password": "request_pass",
                    },
                },
            )

            assert response.status_code == 200
            mock_sync_service.sync_playlist.assert_called_once()
            _, _, url, username, password = (
                mock_sync_service.sync_playlist.call_args.args
            )
            assert url == "http://8.8.8.8:4533"
            assert username == "request_user"
            assert password == "request_pass"
        finally:
            app.dependency_overrides.pop(get_config, None)
            app.dependency_overrides.pop(get_navidrome_sync_service, None)
            app.dependency_overrides.pop(get_active_profile, None)
            app.dependency_overrides.pop(get_profile_database, None)
