import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from vibe_dj.api.dependencies import invalidate_config_cache
from vibe_dj.app import app


class TestConfigRoutes:
    """Test suite for config API routes."""

    @pytest.fixture
    def client(self):
        """Create a TestClient instance for testing."""
        return TestClient(app)

    def test_get_config_returns_current_config(self, client):
        """Test that GET /api/config returns all expected fields."""
        response = client.get("/api/config")

        assert response.status_code == 200
        data = response.json()
        assert "music_library" in data
        assert "navidrome_url" in data
        assert "navidrome_username" in data
        assert "has_navidrome_password" in data

    def test_get_config_never_returns_password(self, client):
        """Test that password is never returned, only has_navidrome_password flag."""
        response = client.get("/api/config")

        assert response.status_code == 200
        data = response.json()
        assert "navidrome_password" not in data
        assert "has_navidrome_password" in data

    def test_validate_path_empty_path(self, client):
        """Test validation of empty path."""
        response = client.post("/api/config/validate-path", json={"path": ""})

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["exists"] is False
        assert "empty" in data["message"].lower()

    def test_validate_path_nonexistent_path(self, client):
        """Test validation of nonexistent path."""
        response = client.post(
            "/api/config/validate-path", json={"path": "/nonexistent/path/to/music"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["exists"] is False
        assert "does not exist" in data["message"]

    def test_validate_path_file_not_directory(self, client):
        """Test validation when path is a file, not a directory."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            response = client.post(
                "/api/config/validate-path", json={"path": temp_file}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert data["exists"] is True
            assert data["is_directory"] is False
            assert "not a directory" in data["message"]
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_validate_path_valid_directory(self, client):
        """Test validation of a valid directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            response = client.post("/api/config/validate-path", json={"path": temp_dir})

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["exists"] is True
            assert data["is_directory"] is True
            assert "valid" in data["message"].lower()

    def test_validate_path_whitespace_trimmed(self, client):
        """Test that whitespace is trimmed from path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            response = client.post(
                "/api/config/validate-path", json={"path": f"  {temp_dir}  "}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True

    @patch("vibe_dj.services.navidrome_client.NavidromeClient.ping")
    def test_navidrome_test_success(self, mock_ping, client):
        """Test successful Navidrome connection test."""
        mock_ping.return_value = True

        response = client.post(
            "/api/navidrome/test",
            json={
                "url": "http://localhost:4533",
                "username": "testuser",
                "password": "testpass",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "successfully" in data["message"].lower()

    @patch("vibe_dj.services.navidrome_client.NavidromeClient.ping")
    def test_navidrome_test_failure(self, mock_ping, client):
        """Test failed Navidrome connection test."""
        mock_ping.return_value = False

        response = client.post(
            "/api/navidrome/test",
            json={
                "url": "http://localhost:4533",
                "username": "testuser",
                "password": "testpass",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    @patch("vibe_dj.services.navidrome_client.NavidromeClient.__init__")
    def test_navidrome_test_exception(self, mock_init, client):
        """Test Navidrome connection test with exception."""
        mock_init.side_effect = Exception("Connection refused")

        response = client.post(
            "/api/navidrome/test",
            json={
                "url": "http://localhost:4533",
                "username": "testuser",
                "password": "testpass",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Connection refused" in data["message"]

    @patch("vibe_dj.services.navidrome_client.NavidromeClient.ping")
    def test_navidrome_test_uses_stored_password_when_not_provided(
        self, mock_ping, client, monkeypatch
    ):
        """Test that stored password is used when password is not provided in request."""
        mock_ping.return_value = True

        # Create a temp directory for music_library (Config validates it exists)
        with tempfile.TemporaryDirectory() as temp_music_dir:
            # Create a temp config file with stored password
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(
                    {
                        "music_library": temp_music_dir,
                        "navidrome_url": "http://localhost:4533",
                        "navidrome_username": "testuser",
                        "navidrome_password": "stored_password",
                    },
                    f,
                )
                temp_path = f.name

            # Mock os.path.exists to return True for "config.json"
            original_exists = os.path.exists

            def mock_exists(path):
                if path == "config.json":
                    return True
                return original_exists(path)

            monkeypatch.setattr("os.path.exists", mock_exists)

            # Mock Config.from_file to load our temp config
            from vibe_dj.models import Config

            original_from_file = Config.from_file

            def mock_from_file(path):
                if path == "config.json":
                    return original_from_file(temp_path)
                return original_from_file(path)

            monkeypatch.setattr("vibe_dj.models.Config.from_file", mock_from_file)
            invalidate_config_cache()

            try:
                # Request without password - should use stored password
                response = client.post(
                    "/api/navidrome/test",
                    json={
                        "url": "http://localhost:4533",
                        "username": "testuser",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "successfully" in data["message"].lower()
            finally:
                Path(temp_path).unlink(missing_ok=True)
                invalidate_config_cache()

    @patch("vibe_dj.services.navidrome_client.NavidromeClient.ping")
    def test_navidrome_test_empty_password_uses_stored(
        self, mock_ping, client, monkeypatch
    ):
        """Test that empty password string falls back to stored password."""
        mock_ping.return_value = True

        # Create a temp directory for music_library (Config validates it exists)
        with tempfile.TemporaryDirectory() as temp_music_dir:
            # Create a temp config file with stored password
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(
                    {
                        "music_library": temp_music_dir,
                        "navidrome_password": "stored_password",
                    },
                    f,
                )
                temp_path = f.name

            # Mock os.path.exists to return True for "config.json"
            original_exists = os.path.exists

            def mock_exists(path):
                if path == "config.json":
                    return True
                return original_exists(path)

            monkeypatch.setattr("os.path.exists", mock_exists)

            # Mock Config.from_file to load our temp config
            from vibe_dj.models import Config

            original_from_file = Config.from_file

            def mock_from_file(path):
                if path == "config.json":
                    return original_from_file(temp_path)
                return original_from_file(path)

            monkeypatch.setattr("vibe_dj.models.Config.from_file", mock_from_file)
            invalidate_config_cache()

            try:
                # Request with empty password - should use stored password
                response = client.post(
                    "/api/navidrome/test",
                    json={
                        "url": "http://localhost:4533",
                        "username": "testuser",
                        "password": "",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
            finally:
                Path(temp_path).unlink(missing_ok=True)
                invalidate_config_cache()

    def test_navidrome_test_fails_when_no_password_anywhere(self, client, monkeypatch):
        """Test that connection test fails when no password provided and none stored."""
        # Create a temp directory for music_library (Config validates it exists)
        with tempfile.TemporaryDirectory() as temp_music_dir:
            # Create a temp config file without password
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(
                    {
                        "music_library": temp_music_dir,
                    },
                    f,
                )
                temp_path = f.name

            # Mock os.path.exists to return True for "config.json"
            original_exists = os.path.exists

            def mock_exists(path):
                if path == "config.json":
                    return True
                return original_exists(path)

            monkeypatch.setattr("os.path.exists", mock_exists)

            # Mock Config.from_file to load our temp config
            from vibe_dj.models import Config

            original_from_file = Config.from_file

            def mock_from_file(path):
                if path == "config.json":
                    return original_from_file(temp_path)
                return original_from_file(path)

            monkeypatch.setattr("vibe_dj.models.Config.from_file", mock_from_file)
            invalidate_config_cache()

            try:
                # Request without password and none stored
                response = client.post(
                    "/api/navidrome/test",
                    json={
                        "url": "http://localhost:4533",
                        "username": "testuser",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
                assert "no password" in data["message"].lower()
            finally:
                Path(temp_path).unlink(missing_ok=True)
                invalidate_config_cache()


class TestUpdateConfigRoutes:
    """Test suite for config update API routes."""

    @pytest.fixture
    def client(self):
        """Create a TestClient instance for testing."""
        return TestClient(app)

    @pytest.fixture
    def temp_config_file(self, monkeypatch):
        """Create a temporary config file and patch the CONFIG_FILE_PATH."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "music_library": "/original/path",
                    "navidrome_url": "http://original.url",
                    "navidrome_username": "original_user",
                    "navidrome_password": "original_pass",
                },
                f,
            )
            temp_path = f.name

        monkeypatch.setattr("vibe_dj.api.routes.config.CONFIG_FILE_PATH", temp_path)

        # Invalidate cache to ensure fresh config is loaded
        invalidate_config_cache()

        yield temp_path

        # Cleanup
        Path(temp_path).unlink(missing_ok=True)
        invalidate_config_cache()

    def test_update_config_music_library_valid_path(self, client, temp_config_file):
        """Test updating music_library with a valid path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            response = client.put(
                "/api/config",
                json={"music_library": temp_dir},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "saved" in data["message"].lower()

            # Verify the file was updated
            with open(temp_config_file) as f:
                saved_config = json.load(f)
            assert saved_config["music_library"] == temp_dir

    def test_update_config_music_library_invalid_path(self, client, temp_config_file):
        """Test updating music_library with an invalid path."""
        response = client.put(
            "/api/config",
            json={"music_library": "/nonexistent/path/to/music"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "does not exist" in data["message"]

    def test_update_config_music_library_file_not_directory(
        self, client, temp_config_file
    ):
        """Test updating music_library with a file path instead of directory."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            response = client.put(
                "/api/config",
                json={"music_library": temp_file},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "not a directory" in data["message"]
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_update_config_navidrome_url(self, client, temp_config_file):
        """Test updating navidrome_url."""
        response = client.put(
            "/api/config",
            json={"navidrome_url": "http://new.url:4533"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify the file was updated
        with open(temp_config_file) as f:
            saved_config = json.load(f)
        assert saved_config["navidrome_url"] == "http://new.url:4533"
        # Original values should be preserved
        assert saved_config["navidrome_username"] == "original_user"
        assert saved_config["navidrome_password"] == "original_pass"

    def test_update_config_navidrome_username(self, client, temp_config_file):
        """Test updating navidrome_username."""
        response = client.put(
            "/api/config",
            json={"navidrome_username": "new_user"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify the file was updated
        with open(temp_config_file) as f:
            saved_config = json.load(f)
        assert saved_config["navidrome_username"] == "new_user"

    def test_update_config_navidrome_password(self, client, temp_config_file):
        """Test updating navidrome_password."""
        response = client.put(
            "/api/config",
            json={"navidrome_password": "new_password"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify the file was updated
        with open(temp_config_file) as f:
            saved_config = json.load(f)
        assert saved_config["navidrome_password"] == "new_password"

    def test_update_config_empty_password_preserves_existing(
        self, client, temp_config_file
    ):
        """Test that empty password preserves existing password."""
        response = client.put(
            "/api/config",
            json={"navidrome_password": ""},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify original password is preserved
        with open(temp_config_file) as f:
            saved_config = json.load(f)
        assert saved_config["navidrome_password"] == "original_pass"

    def test_update_config_partial_update_preserves_other_fields(
        self, client, temp_config_file
    ):
        """Test that partial updates preserve other config fields."""
        response = client.put(
            "/api/config",
            json={"navidrome_url": "http://new.url"},
        )

        assert response.status_code == 200

        # Verify other fields are preserved
        with open(temp_config_file) as f:
            saved_config = json.load(f)
        assert saved_config["music_library"] == "/original/path"
        assert saved_config["navidrome_username"] == "original_user"
        assert saved_config["navidrome_password"] == "original_pass"

    def test_update_config_multiple_fields(self, client, temp_config_file):
        """Test updating multiple fields at once."""
        with tempfile.TemporaryDirectory() as temp_dir:
            response = client.put(
                "/api/config",
                json={
                    "music_library": temp_dir,
                    "navidrome_url": "http://new.url",
                    "navidrome_username": "new_user",
                    "navidrome_password": "new_pass",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

            # Verify all fields were updated
            with open(temp_config_file) as f:
                saved_config = json.load(f)
            assert saved_config["music_library"] == temp_dir
            assert saved_config["navidrome_url"] == "http://new.url"
            assert saved_config["navidrome_username"] == "new_user"
            assert saved_config["navidrome_password"] == "new_pass"

    def test_update_config_empty_request(self, client, temp_config_file):
        """Test that empty request still succeeds (no-op)."""
        response = client.put(
            "/api/config",
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_update_config_clears_url_with_empty_string(self, client, temp_config_file):
        """Test that empty string clears navidrome_url."""
        response = client.put(
            "/api/config",
            json={"navidrome_url": ""},
        )

        assert response.status_code == 200

        with open(temp_config_file) as f:
            saved_config = json.load(f)
        assert saved_config["navidrome_url"] is None
