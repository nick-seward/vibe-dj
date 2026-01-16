import json
import os
import tempfile
import unittest
from pathlib import Path

from vibe_dj.models.config import Config


class TestConfig(unittest.TestCase):
    """Test suite for Config class."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = Config()

        self.assertEqual(config.music_library, "")
        self.assertEqual(config.database_path, "music.db")
        self.assertEqual(config.faiss_index_path, "faiss_index.bin")
        self.assertEqual(config.playlist_output, "playlist.m3u")
        self.assertEqual(config.sample_rate, 22050)
        self.assertEqual(config.max_duration, 180)
        self.assertEqual(config.n_mfcc, 13)
        self.assertEqual(config.parallel_workers, os.cpu_count() or 4)
        self.assertEqual(config.batch_size, 10)

    def test_config_custom_values(self):
        config = Config(
            music_library="",
            database_path="/custom/path.db",
            sample_rate=44100,
            parallel_workers=8,
        )

        self.assertEqual(config.music_library, "")
        self.assertEqual(config.database_path, "/custom/path.db")
        self.assertEqual(config.sample_rate, 44100)
        self.assertEqual(config.parallel_workers, 8)
        self.assertEqual(config.playlist_output, "playlist.m3u")

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

            self.assertEqual(loaded_config.music_library, "")
            self.assertEqual(loaded_config.database_path, "/test/db.db")
            self.assertEqual(loaded_config.sample_rate, 44100)
            self.assertEqual(loaded_config.parallel_workers, 8)
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

        self.assertEqual(config.music_library, "")
        self.assertEqual(config.database_path, "/custom/db.db")
        self.assertEqual(config.sample_rate, 48000)
        self.assertFalse(hasattr(config, "unknown_field"))

    def test_music_library_validation_nonexistent_path(self):
        with self.assertRaises(ValueError) as context:
            Config(music_library="/nonexistent/path/to/music")
        self.assertIn("does not exist", str(context.exception))

    def test_music_library_validation_file_not_directory(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            with self.assertRaises(ValueError) as context:
                Config(music_library=temp_file)
            self.assertIn("not a directory", str(context.exception))
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_music_library_validation_valid_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = Config(music_library=temp_dir)
            self.assertEqual(config.music_library, temp_dir)


if __name__ == "__main__":
    unittest.main()
