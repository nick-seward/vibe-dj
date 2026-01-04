from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from vibe_dj.services.navidrome_client import NavidromeClient


class TestNavidromeClient:
    """Test suite for NavidromeClient class."""

    @pytest.fixture
    def client(self):
        """Create a NavidromeClient instance for testing."""
        return NavidromeClient(
            base_url="http://localhost:4533", username="testuser", password="testpass"
        )

    @pytest.fixture
    def mock_response(self):
        """Create a mock response object."""
        mock = Mock()
        mock.status_code = 200
        mock.raise_for_status = Mock()
        return mock

    def test_init(self, client):
        """Test client initialization."""
        assert client.base_url == "http://localhost:4533"
        assert client.username == "testuser"
        assert client.password == "testpass"
        assert client.client_id == "vibe-dj"
        assert client.api_version == "1.16.1"

    def test_generate_auth_token(self, client):
        """Test authentication token generation."""
        token, salt = client._generate_auth_token()

        assert isinstance(token, str)
        assert isinstance(salt, str)
        assert len(token) == 32
        assert len(salt) == 16

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_call_success(self, mock_get, client, mock_response):
        """Test successful API call."""
        mock_response.json.return_value = {
            "subsonic-response": {"status": "ok", "version": "1.16.1"}
        }
        mock_get.return_value = mock_response

        result = client._call("ping")

        assert result["status"] == "ok"
        assert mock_get.called

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_call_api_error(self, mock_get, client, mock_response):
        """Test API error handling."""
        mock_response.json.return_value = {
            "subsonic-response": {
                "status": "failed",
                "error": {"code": 40, "message": "Wrong username or password"},
            }
        }
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="API error 40"):
            client._call("ping")

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_call_network_error_with_retry(self, mock_get, client):
        """Test network error with retry logic."""
        mock_get.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
        ]

        with pytest.raises(requests.exceptions.Timeout):
            client._call("ping", max_retries=3)

        assert mock_get.call_count == 3

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_call_retry_success(self, mock_get, client, mock_response):
        """Test successful retry after initial failure."""
        mock_response.json.return_value = {"subsonic-response": {"status": "ok"}}

        mock_get.side_effect = [requests.exceptions.Timeout(), mock_response]

        result = client._call("ping", max_retries=3)

        assert result["status"] == "ok"
        assert mock_get.call_count == 2

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_search_song_with_album(self, mock_get, client, mock_response):
        """Test song search with title, artist, and album."""
        mock_response.json.return_value = {
            "subsonic-response": {
                "status": "ok",
                "searchResult3": {
                    "song": [
                        {"id": "song123", "title": "Test Song", "artist": "Test Artist"}
                    ]
                },
            }
        }
        mock_get.return_value = mock_response

        song_id = client.search_song(
            title="Test Song", artist="Test Artist", album="Test Album"
        )

        assert song_id == "song123"
        assert mock_get.called
        call_args = mock_get.call_args
        assert "Test Song Test Artist Test Album" in str(call_args)

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_search_song_fallback_to_title_artist(
        self, mock_get, client, mock_response
    ):
        """Test song search fallback to title + artist."""
        mock_response_empty = Mock()
        mock_response_empty.status_code = 200
        mock_response_empty.raise_for_status = Mock()
        mock_response_empty.json.return_value = {
            "subsonic-response": {"status": "ok", "searchResult3": {}}
        }

        mock_response_found = Mock()
        mock_response_found.status_code = 200
        mock_response_found.raise_for_status = Mock()
        mock_response_found.json.return_value = {
            "subsonic-response": {
                "status": "ok",
                "searchResult3": {"song": [{"id": "song456", "title": "Test Song"}]},
            }
        }

        mock_get.side_effect = [mock_response_empty, mock_response_found]

        song_id = client.search_song(
            title="Test Song", artist="Test Artist", album="Test Album"
        )

        assert song_id == "song456"
        assert mock_get.call_count == 2

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_search_song_no_match(self, mock_get, client, mock_response):
        """Test song search with no matches."""
        mock_response.json.return_value = {
            "subsonic-response": {"status": "ok", "searchResult3": {}}
        }
        mock_get.return_value = mock_response

        song_id = client.search_song(title="Nonexistent Song", artist="Unknown Artist")

        assert song_id is None

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_get_playlists(self, mock_get, client, mock_response):
        """Test getting all playlists."""
        mock_response.json.return_value = {
            "subsonic-response": {
                "status": "ok",
                "playlists": {
                    "playlist": [
                        {"id": "pl1", "name": "Playlist 1", "songCount": 10},
                        {"id": "pl2", "name": "Playlist 2", "songCount": 20},
                    ]
                },
            }
        }
        mock_get.return_value = mock_response

        playlists = client.get_playlists()

        assert len(playlists) == 2
        assert playlists[0]["name"] == "Playlist 1"
        assert playlists[1]["name"] == "Playlist 2"

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_get_playlists_single_result(self, mock_get, client, mock_response):
        """Test getting playlists when only one exists (returns dict not list)."""
        mock_response.json.return_value = {
            "subsonic-response": {
                "status": "ok",
                "playlists": {
                    "playlist": {"id": "pl1", "name": "Playlist 1", "songCount": 10}
                },
            }
        }
        mock_get.return_value = mock_response

        playlists = client.get_playlists()

        assert len(playlists) == 1
        assert playlists[0]["name"] == "Playlist 1"

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_get_playlist_by_name_found(self, mock_get, client, mock_response):
        """Test finding a playlist by name."""
        mock_response.json.return_value = {
            "subsonic-response": {
                "status": "ok",
                "playlists": {
                    "playlist": [
                        {"id": "pl1", "name": "My Playlist", "songCount": 10},
                        {"id": "pl2", "name": "Other Playlist", "songCount": 5},
                    ]
                },
            }
        }
        mock_get.return_value = mock_response

        playlist = client.get_playlist_by_name("My Playlist")

        assert playlist is not None
        assert playlist["id"] == "pl1"
        assert playlist["name"] == "My Playlist"

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_get_playlist_by_name_not_found(self, mock_get, client, mock_response):
        """Test finding a playlist by name when it doesn't exist."""
        mock_response.json.return_value = {
            "subsonic-response": {
                "status": "ok",
                "playlists": {
                    "playlist": [
                        {"id": "pl1", "name": "Other Playlist", "songCount": 5}
                    ]
                },
            }
        }
        mock_get.return_value = mock_response

        playlist = client.get_playlist_by_name("Nonexistent Playlist")

        assert playlist is None

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_create_playlist(self, mock_get, client, mock_response):
        """Test creating a new playlist."""
        mock_response.json.return_value = {
            "subsonic-response": {
                "status": "ok",
                "playlist": {"id": "newpl123", "name": "New Playlist", "songCount": 3},
            }
        }
        mock_get.return_value = mock_response

        playlist_id = client.create_playlist(
            name="New Playlist", song_ids=["song1", "song2", "song3"]
        )

        assert playlist_id == "newpl123"
        assert mock_get.called

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_create_playlist_empty_songs(self, mock_get, client):
        """Test creating a playlist with no songs."""
        playlist_id = client.create_playlist(name="Empty Playlist", song_ids=[])

        assert playlist_id is None
        assert not mock_get.called

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_update_playlist(self, mock_get, client, mock_response):
        """Test updating an existing playlist."""
        mock_response.json.return_value = {"subsonic-response": {"status": "ok"}}
        mock_get.return_value = mock_response

        success = client.update_playlist(
            playlist_id="pl123", name="Updated Name", song_ids_to_add=["song4", "song5"]
        )

        assert success is True
        assert mock_get.called

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_replace_playlist_songs(self, mock_get, client):
        """Test replacing all songs in a playlist."""
        mock_get_playlist = Mock()
        mock_get_playlist.status_code = 200
        mock_get_playlist.raise_for_status = Mock()
        mock_get_playlist.json.return_value = {
            "subsonic-response": {
                "status": "ok",
                "playlist": {"id": "pl123", "entry": [{"id": "old1"}, {"id": "old2"}]},
            }
        }

        mock_update = Mock()
        mock_update.status_code = 200
        mock_update.raise_for_status = Mock()
        mock_update.json.return_value = {"subsonic-response": {"status": "ok"}}

        mock_get.side_effect = [mock_get_playlist, mock_update, mock_update]

        success = client.replace_playlist_songs(
            playlist_id="pl123", song_ids=["new1", "new2", "new3"]
        )

        assert success is True
        assert mock_get.call_count == 3

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_replace_playlist_songs_empty_playlist(self, mock_get, client):
        """Test replacing songs in an empty playlist."""
        mock_get_playlist = Mock()
        mock_get_playlist.status_code = 200
        mock_get_playlist.raise_for_status = Mock()
        mock_get_playlist.json.return_value = {
            "subsonic-response": {
                "status": "ok",
                "playlist": {"id": "pl123", "entry": []},
            }
        }

        mock_update = Mock()
        mock_update.status_code = 200
        mock_update.raise_for_status = Mock()
        mock_update.json.return_value = {"subsonic-response": {"status": "ok"}}

        mock_get.side_effect = [mock_get_playlist, mock_update]

        success = client.replace_playlist_songs(
            playlist_id="pl123", song_ids=["new1", "new2"]
        )

        assert success is True
        assert mock_get.call_count == 2

    @patch("vibe_dj.services.navidrome_client.requests.Session.get")
    def test_search_song_multiple_matches(self, mock_get, client, mock_response):
        """Test that first match is returned when multiple songs match."""
        mock_response.json.return_value = {
            "subsonic-response": {
                "status": "ok",
                "searchResult3": {
                    "song": [
                        {"id": "first", "title": "Test Song"},
                        {"id": "second", "title": "Test Song"},
                        {"id": "third", "title": "Test Song"},
                    ]
                },
            }
        }
        mock_get.return_value = mock_response

        song_id = client.search_song(title="Test Song", artist="Test Artist")

        assert song_id == "first"
