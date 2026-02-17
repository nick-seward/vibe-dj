"""Integration tests for profile database initialization and credential migration."""

import os
import tempfile
from pathlib import Path

import pytest

from vibe_dj.app import _initialize_profiles
from vibe_dj.core.profile_database import ProfileDatabase
from vibe_dj.models import Config


@pytest.fixture()
def migration_env():
    """Set up a temporary profile database and encryption key for migration tests."""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()

    key = ProfileDatabase.generate_key()

    original_db = os.environ.get("VIBE_DJ_PROFILES_DB")
    original_key = os.environ.get("VIBE_DJ_ENCRYPTION_KEY")

    os.environ["VIBE_DJ_PROFILES_DB"] = temp_db.name
    os.environ["VIBE_DJ_ENCRYPTION_KEY"] = key

    yield temp_db.name, key

    if original_db is not None:
        os.environ["VIBE_DJ_PROFILES_DB"] = original_db
    else:
        os.environ.pop("VIBE_DJ_PROFILES_DB", None)

    if original_key is not None:
        os.environ["VIBE_DJ_ENCRYPTION_KEY"] = original_key
    else:
        os.environ.pop("VIBE_DJ_ENCRYPTION_KEY", None)

    Path(temp_db.name).unlink(missing_ok=True)


class TestProfileMigration:
    """Integration tests for _initialize_profiles startup migration."""

    def test_creates_shared_profile_on_fresh_db(self, migration_env):
        """Test that _initialize_profiles creates the 'Shared' profile on a fresh DB."""
        db_path, key = migration_env
        config = Config()

        _initialize_profiles(config)

        with ProfileDatabase(db_path=db_path, encryption_key=key) as db:
            db.init_db()
            profiles = db.get_all_profiles()

        assert len(profiles) == 1
        assert profiles[0].display_name == "Shared"

    def test_migrates_navidrome_credentials_to_shared_profile(self, migration_env):
        """Test that existing Navidrome credentials are migrated to the 'Shared' profile."""
        db_path, key = migration_env
        config = Config(
            navidrome_url="http://navidrome.example.com",
            navidrome_username="testuser",
            navidrome_password="secret123",
        )

        _initialize_profiles(config)

        with ProfileDatabase(db_path=db_path, encryption_key=key) as db:
            db.init_db()
            shared = db.get_profile_by_name("Shared")

        assert shared is not None
        assert shared.subsonic_url == "http://navidrome.example.com"
        assert shared.subsonic_username == "testuser"
        assert shared.subsonic_password_encrypted is not None

        with ProfileDatabase(db_path=db_path, encryption_key=key) as db:
            db.init_db()
            shared = db.get_profile_by_name("Shared")
            decrypted = db.decrypt_password(shared.subsonic_password_encrypted)

        assert decrypted == "secret123"

    def test_migration_is_idempotent(self, migration_env):
        """Test that running _initialize_profiles twice does not duplicate or overwrite data."""
        db_path, key = migration_env
        config = Config(
            navidrome_url="http://navidrome.example.com",
            navidrome_username="testuser",
            navidrome_password="secret123",
        )

        _initialize_profiles(config)
        _initialize_profiles(config)

        with ProfileDatabase(db_path=db_path, encryption_key=key) as db:
            db.init_db()
            profiles = db.get_all_profiles()
            shared = db.get_profile_by_name("Shared")

        assert len(profiles) == 1
        assert shared.subsonic_url == "http://navidrome.example.com"
        assert shared.subsonic_username == "testuser"

    def test_no_migration_when_no_credentials(self, migration_env):
        """Test that migration is skipped when config has no Navidrome credentials."""
        db_path, key = migration_env
        config = Config()

        _initialize_profiles(config)

        with ProfileDatabase(db_path=db_path, encryption_key=key) as db:
            db.init_db()
            shared = db.get_profile_by_name("Shared")

        assert shared is not None
        assert shared.subsonic_url is None
        assert shared.subsonic_username is None
        assert shared.subsonic_password_encrypted is None

    def test_no_migration_when_shared_already_has_credentials(self, migration_env):
        """Test that migration is skipped when 'Shared' profile already has credentials."""
        db_path, key = migration_env

        with ProfileDatabase(db_path=db_path, encryption_key=key) as db:
            db.init_db()
            shared = db.get_profile_by_name("Shared")
            db.update_profile(
                shared.id,
                subsonic_url="http://existing.example.com",
                subsonic_username="existinguser",
                subsonic_password="existingpass",
            )

        config = Config(
            navidrome_url="http://new.example.com",
            navidrome_username="newuser",
            navidrome_password="newpass",
        )

        _initialize_profiles(config)

        with ProfileDatabase(db_path=db_path, encryption_key=key) as db:
            db.init_db()
            shared = db.get_profile_by_name("Shared")

        assert shared.subsonic_url == "http://existing.example.com"
        assert shared.subsonic_username == "existinguser"
