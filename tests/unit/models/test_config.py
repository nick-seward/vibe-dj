import os
import tempfile
from pathlib import Path

import pytest

from vibe_dj.models.config import Config


def test_config_defaults():
    """Test default configuration values."""
    config = Config()

    assert config.music_library == ""
    assert config.database_path == "music.db"
    assert config.faiss_index_path == "faiss_index.bin"
    assert config.playlist_output == "playlist.m3u"
    assert config.sample_rate == 22050
    assert config.max_duration == 180
    assert config.n_mfcc == 13
    assert config.parallel_workers == (os.cpu_count() or 4)
    assert config.batch_size == 10


def test_config_custom_values():
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
    assert config.playlist_output == "playlist.m3u"


def test_save_and_load():
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


def test_from_dict():
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


def test_music_library_validation_nonexistent_path():
    with pytest.raises(ValueError, match="does not exist"):
        Config(music_library="/nonexistent/path/to/music")


def test_music_library_validation_file_not_directory():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_file = f.name

    try:
        with pytest.raises(ValueError, match="not a directory"):
            Config(music_library=temp_file)
    finally:
        Path(temp_file).unlink(missing_ok=True)


def test_music_library_validation_valid_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        config = Config(music_library=temp_dir)
        assert config.music_library == temp_dir
