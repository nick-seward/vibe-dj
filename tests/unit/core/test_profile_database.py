import tempfile
from pathlib import Path

import pytest

from vibe_dj.core.profile_database import ProfileDatabase
from vibe_dj.models.profile import Profile


class TestProfileDatabase:
    """Test suite for ProfileDatabase."""

    @pytest.fixture()
    def db_env(self):
        """Set up test fixtures with temporary database before each test method."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()

        key = ProfileDatabase.generate_key()
        db = ProfileDatabase(temp_db.name, encryption_key=key)
        db.connect()
        db.init_db()

        yield db, key

        db.close()
        Path(temp_db.name).unlink(missing_ok=True)

    def test_context_manager(self, db_env):
        """Test database context manager functionality."""
        db, key = db_env
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()
        try:
            with ProfileDatabase(temp_db.name, encryption_key=key) as ctx_db:
                ctx_db.init_db()
                assert ctx_db.session is not None
        finally:
            Path(temp_db.name).unlink(missing_ok=True)

    def test_session_not_connected_raises(self):
        """Test that accessing session without connecting raises RuntimeError."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()
        try:
            db = ProfileDatabase(temp_db.name)
            with pytest.raises(RuntimeError, match="Database not connected"):
                _ = db.session
        finally:
            Path(temp_db.name).unlink(missing_ok=True)

    def test_init_db_creates_shared_profile(self, db_env):
        """Test that init_db creates the default 'Shared' profile."""
        db, key = db_env
        profiles = db.get_all_profiles()

        assert len(profiles) == 1
        assert profiles[0].display_name == "Shared"

    def test_init_db_idempotent(self, db_env):
        """Test that calling init_db multiple times doesn't duplicate 'Shared'."""
        db, key = db_env
        db.init_db()
        db.init_db()

        profiles = db.get_all_profiles()
        assert len(profiles) == 1

    def test_create_profile(self, db_env):
        """Test creating a new profile."""
        db, key = db_env
        profile = db.create_profile(
            display_name="Nick",
            subsonic_url="http://navidrome.local",
            subsonic_username="nick",
            subsonic_password="secret123",
        )

        assert profile.id is not None
        assert profile.display_name == "Nick"
        assert profile.subsonic_url == "http://navidrome.local"
        assert profile.subsonic_username == "nick"
        assert profile.subsonic_password_encrypted is not None
        assert profile.subsonic_password_encrypted != "secret123"

    def test_create_profile_without_credentials(self, db_env):
        """Test creating a profile without Subsonic credentials."""
        db, key = db_env
        profile = db.create_profile(display_name="Family")

        assert profile.display_name == "Family"
        assert profile.subsonic_url is None
        assert profile.subsonic_username is None
        assert profile.subsonic_password_encrypted is None

    def test_create_profile_duplicate_name_raises(self, db_env):
        """Test that creating a profile with a duplicate name raises ValueError."""
        db, key = db_env
        db.create_profile(display_name="Nick")

        with pytest.raises(ValueError, match="already exists"):
            db.create_profile(display_name="Nick")

    def test_create_profile_duplicate_shared_raises(self, db_env):
        """Test that creating another 'Shared' profile raises ValueError."""
        db, key = db_env
        with pytest.raises(ValueError, match="already exists"):
            db.create_profile(display_name="Shared")

    def test_get_profile(self, db_env):
        """Test retrieving a profile by ID."""
        db, key = db_env
        created = db.create_profile(display_name="Nick")

        retrieved = db.get_profile(created.id)

        assert retrieved is not None
        assert retrieved.display_name == "Nick"

    def test_get_profile_not_found(self, db_env):
        """Test retrieving a non-existent profile returns None."""
        db, key = db_env
        assert db.get_profile(9999) is None

    def test_get_profile_by_name(self, db_env):
        """Test retrieving a profile by display name."""
        db, key = db_env
        db.create_profile(display_name="Nick")

        retrieved = db.get_profile_by_name("Nick")

        assert retrieved is not None
        assert retrieved.display_name == "Nick"

    def test_get_profile_by_name_not_found(self, db_env):
        """Test retrieving a non-existent profile by name returns None."""
        db, key = db_env
        assert db.get_profile_by_name("NonExistent") is None

    def test_get_all_profiles(self, db_env):
        """Test retrieving all profiles."""
        db, key = db_env
        db.create_profile(display_name="Nick")
        db.create_profile(display_name="Family")

        profiles = db.get_all_profiles()

        assert len(profiles) == 3  # Shared + Nick + Family
        names = [p.display_name for p in profiles]
        assert "Shared" in names
        assert "Nick" in names
        assert "Family" in names

    def test_update_profile_display_name(self, db_env):
        """Test updating a profile's display name."""
        db, key = db_env
        created = db.create_profile(display_name="Nick")

        updated = db.update_profile(created.id, display_name="Nicholas")

        assert updated is not None
        assert updated.display_name == "Nicholas"

    def test_update_profile_credentials(self, db_env):
        """Test updating a profile's Subsonic credentials."""
        db, key = db_env
        created = db.create_profile(display_name="Nick")

        updated = db.update_profile(
            created.id,
            subsonic_url="http://new.server",
            subsonic_username="newuser",
            subsonic_password="newpass",
        )

        assert updated is not None
        assert updated.subsonic_url == "http://new.server"
        assert updated.subsonic_username == "newuser"
        assert updated.subsonic_password_encrypted is not None
        decrypted = db.decrypt_password(updated.subsonic_password_encrypted)
        assert decrypted == "newpass"

    def test_update_profile_clear_credentials(self, db_env):
        """Test clearing a profile's credentials by passing empty strings."""
        db, key = db_env
        created = db.create_profile(
            display_name="Nick",
            subsonic_url="http://server",
            subsonic_username="user",
            subsonic_password="pass",
        )

        updated = db.update_profile(
            created.id,
            subsonic_url="",
            subsonic_username="",
            subsonic_password="",
        )

        assert updated is not None
        assert updated.subsonic_url is None
        assert updated.subsonic_username is None
        assert updated.subsonic_password_encrypted is None

    def test_update_profile_not_found(self, db_env):
        """Test updating a non-existent profile returns None."""
        db, key = db_env
        assert db.update_profile(9999, display_name="Ghost") is None

    def test_update_profile_duplicate_name_raises(self, db_env):
        """Test that renaming to an existing name raises ValueError."""
        db, key = db_env
        db.create_profile(display_name="Nick")
        family = db.create_profile(display_name="Family")

        with pytest.raises(ValueError, match="already exists"):
            db.update_profile(family.id, display_name="Nick")

    def test_update_profile_same_name_no_error(self, db_env):
        """Test that updating with the same name doesn't raise."""
        db, key = db_env
        created = db.create_profile(display_name="Nick")

        updated = db.update_profile(created.id, display_name="Nick")

        assert updated is not None
        assert updated.display_name == "Nick"

    def test_delete_profile(self, db_env):
        """Test deleting a profile."""
        db, key = db_env
        created = db.create_profile(display_name="Nick")

        result = db.delete_profile(created.id)

        assert result is True
        assert db.get_profile(created.id) is None

    def test_delete_profile_not_found(self, db_env):
        """Test deleting a non-existent profile returns False."""
        db, key = db_env
        assert db.delete_profile(9999) is False

    def test_delete_shared_profile_raises(self, db_env):
        """Test that deleting the 'Shared' profile raises ValueError."""
        db, key = db_env
        shared = db.get_profile_by_name("Shared")

        with pytest.raises(ValueError, match="cannot be deleted"):
            db.delete_profile(shared.id)

    def test_delete_shared_profile_still_exists(self, db_env):
        """Test that 'Shared' profile still exists after failed delete attempt."""
        db, key = db_env
        shared = db.get_profile_by_name("Shared")

        with pytest.raises(ValueError):
            db.delete_profile(shared.id)

        assert db.get_profile_by_name("Shared") is not None


class TestPasswordEncryption:
    """Test suite for password encryption/decryption."""

    @pytest.fixture()
    def db_env(self):
        """Set up test fixtures with temporary database."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()

        key = ProfileDatabase.generate_key()
        db = ProfileDatabase(temp_db.name, encryption_key=key)
        db.connect()
        db.init_db()

        yield db, key

        db.close()
        Path(temp_db.name).unlink(missing_ok=True)

    def test_encrypt_decrypt_roundtrip(self, db_env):
        """Test that encrypting then decrypting returns the original password."""
        db, key = db_env
        original = "my_secret_password"

        encrypted = db.encrypt_password(original)
        decrypted = db.decrypt_password(encrypted)

        assert decrypted == original
        assert encrypted != original

    def test_encrypted_password_is_different_each_time(self, db_env):
        """Test that Fernet produces different ciphertexts for the same input."""
        db, key = db_env
        password = "same_password"

        encrypted1 = db.encrypt_password(password)
        encrypted2 = db.encrypt_password(password)

        assert encrypted1 != encrypted2
        assert db.decrypt_password(encrypted1) == password
        assert db.decrypt_password(encrypted2) == password

    def test_password_stored_encrypted_in_profile(self, db_env):
        """Test that the password stored in the profile is encrypted."""
        db, key = db_env
        profile = db.create_profile(
            display_name="Nick",
            subsonic_password="plaintext_secret",
        )

        assert profile.subsonic_password_encrypted != "plaintext_secret"
        decrypted = db.decrypt_password(profile.subsonic_password_encrypted)
        assert decrypted == "plaintext_secret"

    def test_same_key_can_decrypt(self, db_env):
        """Test that a new ProfileDatabase with the same key can decrypt."""
        db, key = db_env
        profile = db.create_profile(
            display_name="Nick",
            subsonic_password="secret123",
        )
        encrypted = profile.subsonic_password_encrypted

        temp_db2 = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db2.close()
        try:
            db2 = ProfileDatabase(temp_db2.name, encryption_key=key)
            decrypted = db2.decrypt_password(encrypted)
            assert decrypted == "secret123"
        finally:
            Path(temp_db2.name).unlink(missing_ok=True)

    def test_generate_key_returns_valid_key(self):
        """Test that generate_key returns a valid Fernet key."""
        key = ProfileDatabase.generate_key()

        assert isinstance(key, str)
        assert len(key) == 44  # Base64-encoded 32-byte key

    def test_different_keys_cannot_decrypt(self, db_env):
        """Test that a different key cannot decrypt passwords."""
        db, key = db_env
        encrypted = db.encrypt_password("secret")

        different_key = ProfileDatabase.generate_key()
        temp_db2 = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db2.close()
        try:
            db2 = ProfileDatabase(temp_db2.name, encryption_key=different_key)
            with pytest.raises(Exception):
                db2.decrypt_password(encrypted)
        finally:
            Path(temp_db2.name).unlink(missing_ok=True)

    def test_auto_generated_key_works(self):
        """Test that ProfileDatabase works when no key is provided."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()
        try:
            db = ProfileDatabase(temp_db.name)
            db.connect()
            db.init_db()

            profile = db.create_profile(
                display_name="Nick",
                subsonic_password="auto_key_test",
            )

            decrypted = db.decrypt_password(profile.subsonic_password_encrypted)
            assert decrypted == "auto_key_test"

            db.close()
        finally:
            Path(temp_db.name).unlink(missing_ok=True)


class TestProfileModel:
    """Test suite for the Profile SQLAlchemy model."""

    @pytest.fixture()
    def db_env(self):
        """Set up test fixtures with temporary database."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()

        key = ProfileDatabase.generate_key()
        db = ProfileDatabase(temp_db.name, encryption_key=key)
        db.connect()
        db.init_db()

        yield db

        db.close()
        Path(temp_db.name).unlink(missing_ok=True)

    def test_profile_str(self, db_env):
        """Test Profile __str__ returns display_name."""
        db = db_env
        profile = db.create_profile(display_name="Nick")
        assert str(profile) == "Nick"

    def test_profile_repr(self, db_env):
        """Test Profile __repr__ returns detailed representation."""
        db = db_env
        profile = db.create_profile(display_name="Nick")
        assert "Profile(" in repr(profile)
        assert "Nick" in repr(profile)

    def test_profile_timestamps(self, db_env):
        """Test that created_at and updated_at are set on creation."""
        db = db_env
        profile = db.create_profile(display_name="Nick")

        assert profile.created_at is not None
        assert profile.updated_at is not None
