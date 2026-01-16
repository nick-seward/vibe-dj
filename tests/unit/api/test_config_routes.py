import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

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
            response = client.post(
                "/api/config/validate-path", json={"path": temp_dir}
            )

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
