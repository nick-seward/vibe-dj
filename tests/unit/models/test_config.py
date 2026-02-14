import os
import tempfile
from pathlib import Path

import pytest

from vibe_dj.models.config import (
    ALLOWED_PLAYLIST_SIZES,
    BPM_JITTER_MAX,
    BPM_JITTER_MIN,
    Config,
)


class TestConfig:
    """Test suite for Config model."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = Config()

        assert config.music_library == ""
        assert config.database_path == "music.db"
        assert config.faiss_index_path == "faiss_index.bin"
        assert config.sample_rate == 22050
        assert config.max_duration == 180
        assert config.n_mfcc == 13
        assert config.parallel_workers == (os.cpu_count() or 4)
        assert config.batch_size == 10
        assert config.default_playlist_size == 20
        assert config.default_bpm_jitter == 5.0

    def test_config_custom_values(self):
        config = Config(
            music_library="",
            database_path="/custom/path.db",
            sample_rate=44100,
            parallel_workers=8,
        )

        assert config.music_library == ""
        assert config.database_path == "/custom/path.db"
        assert config.sample_rate == 44100
        assert config.parallel_workers == 8

    def test_save_and_load(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            original_config = Config(
                music_library="",
                database_path="/test/db.db",
                sample_rate=44100,
                parallel_workers=8,
            )
            original_config.save(temp_path)

            loaded_config = Config.from_file(temp_path)

            assert loaded_config.music_library == ""
            assert loaded_config.database_path == "/test/db.db"
            assert loaded_config.sample_rate == 44100
            assert loaded_config.parallel_workers == 8
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_from_dict(self):
        data = {
            "music_library": "",
            "database_path": "/custom/db.db",
            "sample_rate": 48000,
            "unknown_field": "should_be_ignored",
        }

        config = Config.from_dict(data)

        assert config.music_library == ""
        assert config.database_path == "/custom/db.db"
        assert config.sample_rate == 48000
        assert not hasattr(config, "unknown_field")

    def test_music_library_validation_nonexistent_path(self):
        with pytest.raises(ValueError, match="does not exist"):
            Config(music_library="/nonexistent/path/to/music")

    def test_music_library_validation_file_not_directory(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="not a directory"):
                Config(music_library=temp_file)
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_music_library_validation_valid_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(music_library=temp_dir)
            assert config.music_library == temp_dir

    def test_playlist_size_custom_valid(self):
        for size in ALLOWED_PLAYLIST_SIZES:
            config = Config(default_playlist_size=size)
            assert config.default_playlist_size == size

    def test_playlist_size_invalid(self):
        with pytest.raises(ValueError, match="default_playlist_size must be one of"):
            Config(default_playlist_size=10)

    def test_playlist_size_invalid_zero(self):
        with pytest.raises(ValueError, match="default_playlist_size must be one of"):
            Config(default_playlist_size=0)

    def test_bpm_jitter_custom_valid(self):
        config = Config(default_bpm_jitter=10.0)
        assert config.default_bpm_jitter == 10.0

    def test_bpm_jitter_at_boundaries(self):
        config_min = Config(default_bpm_jitter=BPM_JITTER_MIN)
        assert config_min.default_bpm_jitter == BPM_JITTER_MIN

        config_max = Config(default_bpm_jitter=BPM_JITTER_MAX)
        assert config_max.default_bpm_jitter == BPM_JITTER_MAX

    def test_bpm_jitter_below_min(self):
        with pytest.raises(ValueError, match="default_bpm_jitter must be between"):
            Config(default_bpm_jitter=0.5)

    def test_bpm_jitter_above_max(self):
        with pytest.raises(ValueError, match="default_bpm_jitter must be between"):
            Config(default_bpm_jitter=25.0)

    def test_save_and_load_playlist_defaults(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            original = Config(
                music_library="",
                default_playlist_size=30,
                default_bpm_jitter=8.5,
            )
            original.save(temp_path)
            loaded = Config.from_file(temp_path)

            assert loaded.default_playlist_size == 30
            assert loaded.default_bpm_jitter == 8.5
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_from_dict_playlist_defaults(self):
        data = {
            "music_library": "",
            "default_playlist_size": 40,
            "default_bpm_jitter": 15.0,
        }
        config = Config.from_dict(data)
        assert config.default_playlist_size == 40
        assert config.default_bpm_jitter == 15.0
