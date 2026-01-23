from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from vibe_dj.models import Config, Playlist, Song
from vibe_dj.services.navidrome_client import NavidromeClient
from vibe_dj.services.navidrome_sync_service import NavidromeSyncService


class TestNavidromeSyncService:
    """Test suite for NavidromeSyncService class."""

    @pytest.fixture
    def config(self):
        """Create a Config instance for testing."""
        cfg = Config()
        cfg.navidrome_url = "http://config-url:4533"
        cfg.navidrome_username = "config_user"
        cfg.navidrome_password = "config_pass"
        return cfg

    @pytest.fixture
    def service(self, config):
        """Create a NavidromeSyncService instance for testing."""
        return NavidromeSyncService(config)

    @pytest.fixture
    def mock_playlist(self):
        """Create a mock playlist with test songs."""
        song1 = Song(
            id=1,
            file_path="/music/song1.mp3",
            title="Test Song 1",
            artist="Test Artist 1",
            album="Test Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        song2 = Song(
            id=2,
            file_path="/music/song2.mp3",
            title="Test Song 2",
            artist="Test Artist 2",
            album="Test Album 2",
            genre="Pop",
            last_modified=0.0,
            duration=200,
        )
        song3 = Song(
            id=3,
            file_path="/music/song3.mp3",
            title="Test Song 3",
            artist="Test Artist 3",
            album="Test Album 3",
            genre="Jazz",
            last_modified=0.0,
            duration=220,
        )

        playlist = Playlist(seed_songs=[song1])
        playlist.songs = [song1, song2, song3]
        return playlist

    def test_init(self, service, config):
        """Test service initialization."""
        assert service.config == config

    @patch("vibe_dj.services.navidrome_sync_service.NavidromeClient")
    def test_sync_playlist_success_create_new(
        self, mock_client_class, service, mock_playlist
    ):
        """Test successful playlist creation on Navidrome."""
        mock_client = Mock(spec=NavidromeClient)
        mock_client_class.return_value = mock_client

        mock_client.search_song.side_effect = ["song_id_1", "song_id_2", "song_id_3"]
        mock_client.get_playlist_by_name.return_value = None
        mock_client.create_playlist.return_value = "new_playlist_id"

        result = service.sync_playlist(
            playlist=mock_playlist,
            output_path="/playlists/test.m3u",
            playlist_name="Test Playlist",
        )

        assert result["success"] is True
        assert result["playlist_id"] == "new_playlist_id"
        assert result["playlist_name"] == "Test Playlist"
        assert result["matched_count"] == 3
        assert result["total_count"] == 3
        assert result["skipped_songs"] == []
        assert result["error"] is None
        assert result["action"] == "created"

        mock_client.create_playlist.assert_called_once_with(
            "Test Playlist", ["song_id_1", "song_id_2", "song_id_3"]
        )

    @patch("vibe_dj.services.navidrome_sync_service.NavidromeClient")
    def test_sync_playlist_success_update_existing(
        self, mock_client_class, service, mock_playlist
    ):
        """Test successful playlist update on Navidrome."""
        mock_client = Mock(spec=NavidromeClient)
        mock_client_class.return_value = mock_client

        mock_client.search_song.side_effect = ["song_id_1", "song_id_2", "song_id_3"]
        mock_client.get_playlist_by_name.return_value = {
            "id": "existing_id",
            "name": "Test Playlist",
        }
        mock_client.replace_playlist_songs.return_value = True

        result = service.sync_playlist(
            playlist=mock_playlist,
            output_path="/playlists/test.m3u",
            playlist_name="Test Playlist",
        )

        assert result["success"] is True
        assert result["playlist_id"] == "existing_id"
        assert result["playlist_name"] == "Test Playlist"
        assert result["matched_count"] == 3
        assert result["total_count"] == 3
        assert result["skipped_songs"] == []
        assert result["error"] is None
        assert result["action"] == "updated"

        mock_client.replace_playlist_songs.assert_called_once_with(
            "existing_id", ["song_id_1", "song_id_2", "song_id_3"]
        )

    @patch("vibe_dj.services.navidrome_sync_service.NavidromeClient")
    def test_sync_playlist_partial_match(
        self, mock_client_class, service, mock_playlist
    ):
        """Test playlist sync with some songs not matched."""
        mock_client = Mock(spec=NavidromeClient)
        mock_client_class.return_value = mock_client

        mock_client.search_song.side_effect = ["song_id_1", None, "song_id_3"]
        mock_client.get_playlist_by_name.return_value = None
        mock_client.create_playlist.return_value = "new_playlist_id"

        result = service.sync_playlist(
            playlist=mock_playlist,
            output_path="/playlists/test.m3u",
            playlist_name="Test Playlist",
        )

        assert result["success"] is True
        assert result["matched_count"] == 2
        assert result["total_count"] == 3
        assert len(result["skipped_songs"]) == 1
        assert result["skipped_songs"][0] == "Test Song 2 by Test Artist 2"

        mock_client.create_playlist.assert_called_once_with(
            "Test Playlist", ["song_id_1", "song_id_3"]
        )

    @patch("vibe_dj.services.navidrome_sync_service.NavidromeClient")
    def test_sync_playlist_no_matches(self, mock_client_class, service, mock_playlist):
        """Test playlist sync when no songs are matched."""
        mock_client = Mock(spec=NavidromeClient)
        mock_client_class.return_value = mock_client

        mock_client.search_song.return_value = None

        result = service.sync_playlist(
            playlist=mock_playlist,
            output_path="/playlists/test.m3u",
            playlist_name="Test Playlist",
        )

        assert result["success"] is False
        assert result["playlist_id"] is None
        assert result["matched_count"] == 0
        assert result["total_count"] == 3
        assert len(result["skipped_songs"]) == 3
        assert result["error"] == "No songs matched"
        assert result["action"] is None

    def test_sync_playlist_missing_credentials(self, service, mock_playlist):
        """Test playlist sync with missing credentials."""
        service.config.navidrome_url = None
        service.config.navidrome_username = None
        service.config.navidrome_password = None

        result = service.sync_playlist(
            playlist=mock_playlist, output_path="/playlists/test.m3u"
        )

        assert result["success"] is False
        assert result["error"] == "Missing credentials"
        assert result["matched_count"] == 0
        assert result["action"] is None

    @patch("vibe_dj.services.navidrome_sync_service.NavidromeClient")
    def test_credential_resolution_config(
        self, mock_client_class, service, mock_playlist
    ):
        """Test credential resolution from config file."""
        mock_client = Mock(spec=NavidromeClient)
        mock_client_class.return_value = mock_client
        mock_client.search_song.return_value = "song_id"
        mock_client.get_playlist_by_name.return_value = None
        mock_client.create_playlist.return_value = "playlist_id"

        result = service.sync_playlist(
            playlist=mock_playlist, output_path="/playlists/test.m3u"
        )

        assert result["success"] is True
        mock_client_class.assert_called_once_with(
            "http://config-url:4533", "config_user", "config_pass"
        )

    @patch("vibe_dj.services.navidrome_sync_service.NavidromeClient")
    def test_credential_resolution_priority_params_over_config(
        self, mock_client_class, service, mock_playlist
    ):
        """Test that explicit parameters take priority over config file values."""
        mock_client = Mock(spec=NavidromeClient)
        mock_client_class.return_value = mock_client
        mock_client.search_song.return_value = "song_id"
        mock_client.get_playlist_by_name.return_value = None
        mock_client.create_playlist.return_value = "playlist_id"

        result = service.sync_playlist(
            playlist=mock_playlist,
            output_path="/playlists/test.m3u",
            navidrome_url="http://param-url:4533",
            navidrome_username="param_user",
            navidrome_password="param_pass",
        )

        assert result["success"] is True
        mock_client_class.assert_called_once_with(
            "http://param-url:4533", "param_user", "param_pass"
        )

    @patch("vibe_dj.services.navidrome_sync_service.NavidromeClient")
    def test_playlist_name_defaults_to_filename(
        self, mock_client_class, service, mock_playlist
    ):
        """Test that playlist name defaults to output filename stem."""
        mock_client = Mock(spec=NavidromeClient)
        mock_client_class.return_value = mock_client
        mock_client.search_song.return_value = "song_id"
        mock_client.get_playlist_by_name.return_value = None
        mock_client.create_playlist.return_value = "playlist_id"

        result = service.sync_playlist(
            playlist=mock_playlist, output_path="/playlists/my_awesome_playlist.m3u"
        )

        assert result["success"] is True
        assert result["playlist_name"] == "my_awesome_playlist"
        mock_client.create_playlist.assert_called_once_with(
            "my_awesome_playlist", ["song_id", "song_id", "song_id"]
        )

    @patch("vibe_dj.services.navidrome_sync_service.NavidromeClient")
    def test_sync_playlist_update_failure(
        self, mock_client_class, service, mock_playlist
    ):
        """Test playlist update failure."""
        mock_client = Mock(spec=NavidromeClient)
        mock_client_class.return_value = mock_client

        mock_client.search_song.side_effect = ["song_id_1", "song_id_2", "song_id_3"]
        mock_client.get_playlist_by_name.return_value = {
            "id": "existing_id",
            "name": "Test Playlist",
        }
        mock_client.replace_playlist_songs.return_value = False

        result = service.sync_playlist(
            playlist=mock_playlist,
            output_path="/playlists/test.m3u",
            playlist_name="Test Playlist",
        )

        assert result["success"] is False
        assert result["playlist_id"] == "existing_id"
        assert result["error"] == "Update failed"
        assert result["action"] is None

    @patch("vibe_dj.services.navidrome_sync_service.NavidromeClient")
    def test_sync_playlist_create_failure(
        self, mock_client_class, service, mock_playlist
    ):
        """Test playlist creation failure."""
        mock_client = Mock(spec=NavidromeClient)
        mock_client_class.return_value = mock_client

        mock_client.search_song.side_effect = ["song_id_1", "song_id_2", "song_id_3"]
        mock_client.get_playlist_by_name.return_value = None
        mock_client.create_playlist.return_value = None

        result = service.sync_playlist(
            playlist=mock_playlist,
            output_path="/playlists/test.m3u",
            playlist_name="Test Playlist",
        )

        assert result["success"] is False
        assert result["playlist_id"] is None
        assert result["error"] == "Creation failed"
        assert result["action"] is None

    @patch("vibe_dj.services.navidrome_sync_service.NavidromeClient")
    def test_sync_playlist_client_exception(
        self, mock_client_class, service, mock_playlist
    ):
        """Test handling of NavidromeClient exceptions."""
        mock_client = Mock(spec=NavidromeClient)
        mock_client_class.return_value = mock_client

        mock_client.search_song.side_effect = Exception("Network error")

        result = service.sync_playlist(
            playlist=mock_playlist,
            output_path="/playlists/test.m3u",
            playlist_name="Test Playlist",
        )

        assert result["success"] is False
        assert result["error"] == "Network error"
        assert result["matched_count"] == 0
        assert result["action"] is None

    @patch("vibe_dj.services.navidrome_sync_service.NavidromeClient")
    def test_sync_playlist_many_skipped_songs(self, mock_client_class, service):
        """Test playlist sync with many skipped songs (>5)."""
        songs = []
        for i in range(10):
            song = Song(
                id=i,
                file_path=f"/music/song{i}.mp3",
                title=f"Song {i}",
                artist=f"Artist {i}",
                album=f"Album {i}",
                genre="Rock",
                last_modified=0.0,
                duration=180,
            )
            songs.append(song)

        playlist = Playlist(seed_songs=[songs[0]])
        playlist.songs = songs

        mock_client = Mock(spec=NavidromeClient)
        mock_client_class.return_value = mock_client

        mock_client.search_song.side_effect = [None] * 10

        result = service.sync_playlist(
            playlist=playlist,
            output_path="/playlists/test.m3u",
            playlist_name="Test Playlist",
        )

        assert result["success"] is False
        assert len(result["skipped_songs"]) == 10
        assert result["error"] == "No songs matched"

    @patch("vibe_dj.services.navidrome_sync_service.NavidromeClient")
    def test_sync_playlist_partial_credentials(
        self, mock_client_class, service, mock_playlist
    ):
        """Test playlist sync with only some credentials provided."""
        service.config.navidrome_url = "http://config-url:4533"
        service.config.navidrome_username = None
        service.config.navidrome_password = None

        result = service.sync_playlist(
            playlist=mock_playlist,
            output_path="/playlists/test.m3u",
            navidrome_username="param_user",
        )

        assert result["success"] is False
        assert result["error"] == "Missing credentials"
