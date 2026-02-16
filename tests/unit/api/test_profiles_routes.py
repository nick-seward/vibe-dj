"""Tests for profile API routes."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, PropertyMock

from vibe_dj.api.dependencies import get_profile_database
from vibe_dj.app import app
from vibe_dj.models.profile import Profile


def _make_profile(
    id=1,
    display_name="Test",
    subsonic_url=None,
    subsonic_username=None,
    subsonic_password_encrypted=None,
):
    """Create a mock Profile object with sensible defaults."""
    profile = MagicMock(spec=Profile)
    profile.id = id
    profile.display_name = display_name
    profile.subsonic_url = subsonic_url
    profile.subsonic_username = subsonic_username
    profile.subsonic_password_encrypted = subsonic_password_encrypted
    profile.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    profile.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return profile


class TestListProfiles:
    """Test GET /api/profiles endpoint."""

    def test_list_profiles_empty(self, client):
        """Test listing profiles when none exist."""
        mock_db = MagicMock()
        mock_db.get_all_profiles.return_value = []

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.get("/api/profiles")
            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.pop(get_profile_database, None)

    def test_list_profiles_returns_all(self, client):
        """Test listing multiple profiles."""
        mock_db = MagicMock()
        mock_db.get_all_profiles.return_value = [
            _make_profile(id=1, display_name="Shared"),
            _make_profile(id=2, display_name="Nick"),
        ]

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.get("/api/profiles")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["display_name"] == "Shared"
            assert data[1]["display_name"] == "Nick"
        finally:
            app.dependency_overrides.pop(get_profile_database, None)

    def test_list_profiles_hides_password(self, client):
        """Test that encrypted password is not returned, only has_subsonic_password flag."""
        mock_db = MagicMock()
        mock_db.get_all_profiles.return_value = [
            _make_profile(
                id=1,
                display_name="WithPass",
                subsonic_password_encrypted="encrypted_value",
            ),
        ]

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.get("/api/profiles")
            assert response.status_code == 200
            data = response.json()
            assert data[0]["has_subsonic_password"] is True
            assert "subsonic_password_encrypted" not in data[0]
            assert "subsonic_password" not in data[0]
        finally:
            app.dependency_overrides.pop(get_profile_database, None)


class TestGetProfile:
    """Test GET /api/profiles/{profile_id} endpoint."""

    def test_get_profile_success(self, client):
        """Test getting a profile by ID."""
        mock_db = MagicMock()
        mock_db.get_profile.return_value = _make_profile(
            id=1,
            display_name="Shared",
            subsonic_url="http://navidrome.local",
            subsonic_username="admin",
        )

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.get("/api/profiles/1")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["display_name"] == "Shared"
            assert data["subsonic_url"] == "http://navidrome.local"
            assert data["subsonic_username"] == "admin"
            assert data["has_subsonic_password"] is False
        finally:
            app.dependency_overrides.pop(get_profile_database, None)

    def test_get_profile_not_found(self, client):
        """Test getting a non-existent profile."""
        mock_db = MagicMock()
        mock_db.get_profile.return_value = None

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.get("/api/profiles/999")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_profile_database, None)


class TestCreateProfile:
    """Test POST /api/profiles endpoint."""

    def test_create_profile_minimal(self, client):
        """Test creating a profile with only display_name."""
        mock_db = MagicMock()
        mock_db.create_profile.return_value = _make_profile(id=2, display_name="Nick")

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.post(
                "/api/profiles",
                json={"display_name": "Nick"},
            )
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == 2
            assert data["display_name"] == "Nick"
            mock_db.create_profile.assert_called_once_with(
                display_name="Nick",
                subsonic_url=None,
                subsonic_username=None,
                subsonic_password=None,
            )
        finally:
            app.dependency_overrides.pop(get_profile_database, None)

    def test_create_profile_with_credentials(self, client):
        """Test creating a profile with full Subsonic credentials."""
        mock_db = MagicMock()
        mock_db.create_profile.return_value = _make_profile(
            id=3,
            display_name="Family",
            subsonic_url="http://navidrome.local",
            subsonic_username="family",
            subsonic_password_encrypted="encrypted",
        )

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.post(
                "/api/profiles",
                json={
                    "display_name": "Family",
                    "subsonic_url": "http://navidrome.local",
                    "subsonic_username": "family",
                    "subsonic_password": "secret123",
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["display_name"] == "Family"
            assert data["has_subsonic_password"] is True
            mock_db.create_profile.assert_called_once_with(
                display_name="Family",
                subsonic_url="http://navidrome.local",
                subsonic_username="family",
                subsonic_password="secret123",
            )
        finally:
            app.dependency_overrides.pop(get_profile_database, None)

    def test_create_profile_duplicate_name(self, client):
        """Test creating a profile with a duplicate display name."""
        mock_db = MagicMock()
        mock_db.create_profile.side_effect = ValueError(
            "Profile with name 'Shared' already exists"
        )

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.post(
                "/api/profiles",
                json={"display_name": "Shared"},
            )
            assert response.status_code == 409
        finally:
            app.dependency_overrides.pop(get_profile_database, None)


class TestUpdateProfile:
    """Test PUT /api/profiles/{profile_id} endpoint."""

    def test_update_profile_display_name(self, client):
        """Test updating a profile's display name."""
        mock_db = MagicMock()
        mock_db.update_profile.return_value = _make_profile(
            id=2, display_name="Nicholas"
        )

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.put(
                "/api/profiles/2",
                json={"display_name": "Nicholas"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["display_name"] == "Nicholas"
        finally:
            app.dependency_overrides.pop(get_profile_database, None)

    def test_update_profile_not_found(self, client):
        """Test updating a non-existent profile."""
        mock_db = MagicMock()
        mock_db.update_profile.return_value = None

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.put(
                "/api/profiles/999",
                json={"display_name": "Ghost"},
            )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_profile_database, None)

    def test_update_profile_name_conflict(self, client):
        """Test updating a profile with a conflicting display name."""
        mock_db = MagicMock()
        mock_db.update_profile.side_effect = ValueError(
            "Profile with name 'Shared' already exists"
        )

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.put(
                "/api/profiles/2",
                json={"display_name": "Shared"},
            )
            assert response.status_code == 409
        finally:
            app.dependency_overrides.pop(get_profile_database, None)


class TestDeleteProfile:
    """Test DELETE /api/profiles/{profile_id} endpoint."""

    def test_delete_profile_success(self, client):
        """Test deleting a regular profile."""
        mock_db = MagicMock()
        mock_db.delete_profile.return_value = True

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.delete("/api/profiles/2")
            assert response.status_code == 204
        finally:
            app.dependency_overrides.pop(get_profile_database, None)

    def test_delete_profile_not_found(self, client):
        """Test deleting a non-existent profile."""
        mock_db = MagicMock()
        mock_db.delete_profile.return_value = False

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.delete("/api/profiles/999")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_profile_database, None)

    def test_delete_shared_profile_forbidden(self, client):
        """Test that deleting the 'Shared' profile is forbidden."""
        mock_db = MagicMock()
        mock_db.delete_profile.side_effect = ValueError(
            "The 'Shared' profile cannot be deleted"
        )

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.delete("/api/profiles/1")
            assert response.status_code == 403
            data = response.json()
            error_msg = data.get("detail") or data.get("error", "")
            assert "Shared" in error_msg
        finally:
            app.dependency_overrides.pop(get_profile_database, None)


class TestGetActiveProfile:
    """Test the get_active_profile dependency via header."""

    def test_active_profile_header_not_provided(self, client):
        """Test that requests without X-Active-Profile header work normally."""
        mock_db = MagicMock()
        mock_db.get_all_profiles.return_value = []

        def override():
            yield mock_db

        app.dependency_overrides[get_profile_database] = override

        try:
            response = client.get("/api/profiles")
            assert response.status_code == 200
        finally:
            app.dependency_overrides.pop(get_profile_database, None)
