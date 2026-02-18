from cryptography.fernet import Fernet

from vibe_dj.api.dependencies import _load_or_create_encryption_key


class TestLoadOrCreateEncryptionKey:
    """Test encryption key loading and auto-generation logic."""

    def test_returns_env_var_when_set(self, monkeypatch, tmp_path):
        """Test that VIBE_DJ_ENCRYPTION_KEY env var takes priority."""
        expected_key = Fernet.generate_key().decode()
        monkeypatch.setenv("VIBE_DJ_ENCRYPTION_KEY", expected_key)

        db_path = str(tmp_path / "profiles.db")
        result = _load_or_create_encryption_key(db_path)

        assert result == expected_key
        assert not (tmp_path / "encryption.key").exists()

    def test_generates_key_file_when_missing(self, monkeypatch, tmp_path):
        """Test that a key file is created when none exists and no env var set."""
        monkeypatch.delenv("VIBE_DJ_ENCRYPTION_KEY", raising=False)

        db_path = str(tmp_path / "profiles.db")
        result = _load_or_create_encryption_key(db_path)

        key_file = tmp_path / "encryption.key"
        assert key_file.exists()
        assert key_file.read_text().strip() == result
        Fernet(result.encode())

    def test_loads_existing_key_file(self, monkeypatch, tmp_path):
        """Test that an existing key file is loaded rather than regenerated."""
        monkeypatch.delenv("VIBE_DJ_ENCRYPTION_KEY", raising=False)

        existing_key = Fernet.generate_key().decode()
        key_file = tmp_path / "encryption.key"
        key_file.write_text(existing_key)

        db_path = str(tmp_path / "profiles.db")
        result = _load_or_create_encryption_key(db_path)

        assert result == existing_key

    def test_generated_key_is_stable_across_calls(self, monkeypatch, tmp_path):
        """Test that repeated calls return the same key once file is created."""
        monkeypatch.delenv("VIBE_DJ_ENCRYPTION_KEY", raising=False)

        db_path = str(tmp_path / "profiles.db")
        key1 = _load_or_create_encryption_key(db_path)
        key2 = _load_or_create_encryption_key(db_path)

        assert key1 == key2

    def test_generated_key_is_valid_fernet_key(self, monkeypatch, tmp_path):
        """Test that the auto-generated key is a valid Fernet key."""
        monkeypatch.delenv("VIBE_DJ_ENCRYPTION_KEY", raising=False)

        db_path = str(tmp_path / "profiles.db")
        key = _load_or_create_encryption_key(db_path)

        f = Fernet(key.encode())
        token = f.encrypt(b"test data")
        assert f.decrypt(token) == b"test data"

    def test_key_file_placed_alongside_db(self, monkeypatch, tmp_path):
        """Test that encryption.key is placed in the same directory as the db."""
        monkeypatch.delenv("VIBE_DJ_ENCRYPTION_KEY", raising=False)

        subdir = tmp_path / "data"
        subdir.mkdir()
        db_path = str(subdir / "profiles.db")

        _load_or_create_encryption_key(db_path)

        assert (subdir / "encryption.key").exists()
        assert not (tmp_path / "encryption.key").exists()
