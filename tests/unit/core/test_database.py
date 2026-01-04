import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

from vibe_dj.core.database import MusicDatabase
from vibe_dj.models import Config, Features, Song


class TestMusicDatabase(unittest.TestCase):
    """Test suite for MusicDatabase class."""

    def setUp(self):
        """Set up test fixtures with temporary database before each test method."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        self.config = Config(database_path=self.temp_db.name)
        self.db = MusicDatabase(self.config)
        self.db.connect()
        self.db.init_db()

        self.test_song = Song(
            id=0,
            file_path="/test/song.mp3",
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            genre="Rock",
            last_modified=1234567890.0,
            duration=180,
        )

        self.test_features = Features(
            song_id=0,
            feature_vector=np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32),
            bpm=120.5,
        )

    def tearDown(self):
        """Clean up temporary database after each test method."""
        self.db.close()
        Path(self.temp_db.name).unlink(missing_ok=True)

    def test_context_manager(self):
        """Test database context manager functionality."""
        with MusicDatabase(self.config) as db:
            db.init_db()
            self.assertIsNotNone(db.connection)

    def test_init_db(self):
        """Test database schema initialization."""
        cur = self.db.connection.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]

        self.assertIn("songs", tables)
        self.assertIn("features", tables)

    def test_add_song_without_features(self):
        """Test adding a song without features."""
        song_id = self.db.add_song(self.test_song)

        self.assertIsInstance(song_id, int)
        self.assertGreater(song_id, 0)

        retrieved = self.db.get_song(song_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Test Song")
        self.assertEqual(retrieved.artist, "Test Artist")

    def test_add_song_with_features(self):
        """Test adding a song with features."""
        song_id = self.db.add_song(self.test_song, self.test_features)

        retrieved_song = self.db.get_song(song_id)
        retrieved_features = self.db.get_features(song_id)

        self.assertIsNotNone(retrieved_song)
        self.assertIsNotNone(retrieved_features)
        self.assertEqual(retrieved_features.bpm, 120.5)
        np.testing.assert_array_almost_equal(
            retrieved_features.feature_vector, self.test_features.feature_vector
        )

    def test_get_song_by_path(self):
        """Test retrieving a song by its file path."""
        song_id = self.db.add_song(self.test_song)

        retrieved = self.db.get_song_by_path("/test/song.mp3")

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Test Song")

    def test_find_songs_by_title(self):
        """Test finding songs by partial title match."""
        song1 = Song(
            id=0,
            file_path="/test/1.mp3",
            title="Rock Song",
            artist="Artist 1",
            album="Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        song2 = Song(
            id=0,
            file_path="/test/2.mp3",
            title="Another Rock Track",
            artist="Artist 2",
            album="Album 2",
            genre="Rock",
            last_modified=0.0,
            duration=200,
        )
        song3 = Song(
            id=0,
            file_path="/test/3.mp3",
            title="Pop Song",
            artist="Artist 3",
            album="Album 3",
            genre="Pop",
            last_modified=0.0,
            duration=190,
        )

        self.db.add_song(song1)
        self.db.add_song(song2)
        self.db.add_song(song3)

        results = self.db.find_songs_by_title("Rock")

        self.assertEqual(len(results), 2)
        titles = [s.title for s in results]
        self.assertIn("Rock Song", titles)
        self.assertIn("Another Rock Track", titles)

    def test_find_song_exact(self):
        song1 = Song(
            id=0,
            file_path="/test/1.mp3",
            title="Test Song",
            artist="Artist 1",
            album="Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        song2 = Song(
            id=0,
            file_path="/test/2.mp3",
            title="Test Song",
            artist="Artist 2",
            album="Album 2",
            genre="Rock",
            last_modified=0.0,
            duration=200,
        )

        self.db.add_song(song1)
        self.db.add_song(song2)

        result = self.db.find_song_exact("Test Song", "Artist 1", "Album 1")

        self.assertIsNotNone(result)
        self.assertEqual(result.title, "Test Song")
        self.assertEqual(result.artist, "Artist 1")
        self.assertEqual(result.album, "Album 1")

    def test_find_song_exact_no_match(self):
        song1 = Song(
            id=0,
            file_path="/test/1.mp3",
            title="Test Song",
            artist="Artist 1",
            album="Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )

        self.db.add_song(song1)

        result = self.db.find_song_exact("Test Song", "Wrong Artist", "Album 1")

        self.assertIsNone(result)

    def test_get_song_with_features(self):
        song_id = self.db.add_song(self.test_song, self.test_features)

        result = self.db.get_song_with_features(song_id)

        self.assertIsNotNone(result)
        song, features = result
        self.assertEqual(song.title, "Test Song")
        self.assertEqual(features.bpm, 120.5)

    def test_get_all_songs_with_features(self):
        song1 = Song(
            id=0,
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        features1 = Features(
            song_id=0, feature_vector=np.array([1.0, 2.0], dtype=np.float32), bpm=120.0
        )

        song2 = Song(
            id=0,
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            last_modified=0.0,
            duration=200,
        )
        features2 = Features(
            song_id=0, feature_vector=np.array([3.0, 4.0], dtype=np.float32), bpm=130.0
        )

        self.db.add_song(song1, features1)
        self.db.add_song(song2, features2)

        results = self.db.get_all_songs_with_features()

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0].title, "Song 1")
        self.assertEqual(results[1][0].title, "Song 2")

    def test_delete_song(self):
        song_id = self.db.add_song(self.test_song)

        result = self.db.delete_song("/test/song.mp3")

        self.assertTrue(result)
        self.assertIsNone(self.db.get_song(song_id))

    def test_delete_nonexistent_song(self):
        result = self.db.delete_song("/nonexistent/song.mp3")

        self.assertFalse(result)

    def test_get_songs_by_ids(self):
        song1 = Song(
            id=0,
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        song2 = Song(
            id=0,
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            last_modified=0.0,
            duration=200,
        )

        id1 = self.db.add_song(song1)
        id2 = self.db.add_song(song2)

        results = self.db.get_songs_by_ids([id1, id2])

        self.assertEqual(len(results), 2)
        titles = [s.title for s in results]
        self.assertIn("Song 1", titles)
        self.assertIn("Song 2", titles)

    def test_get_all_file_paths_with_mtime(self):
        self.db.add_song(self.test_song)

        paths = self.db.get_all_file_paths_with_mtime()

        self.assertIn("/test/song.mp3", paths)
        self.assertEqual(paths["/test/song.mp3"], 1234567890.0)

    def test_get_songs_without_features(self):
        song1 = Song(
            id=0,
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        song2 = Song(
            id=0,
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            last_modified=0.0,
            duration=200,
        )
        features = Features(
            song_id=0, feature_vector=np.array([1.0, 2.0], dtype=np.float32), bpm=120.0
        )

        self.db.add_song(song1, features)
        self.db.add_song(song2)

        songs_without = self.db.get_songs_without_features()

        self.assertEqual(len(songs_without), 1)
        self.assertEqual(songs_without[0].title, "Song 2")

    def test_get_songs_without_features_filtered(self):
        song1 = Song(
            id=0,
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        song2 = Song(
            id=0,
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            last_modified=0.0,
            duration=200,
        )
        song3 = Song(
            id=0,
            file_path="/test/3.mp3",
            title="Song 3",
            artist="Artist 3",
            album="Album 3",
            genre="Jazz",
            last_modified=0.0,
            duration=210,
        )

        self.db.add_song(song1)
        self.db.add_song(song2)
        self.db.add_song(song3)

        songs_without = self.db.get_songs_without_features(
            ["/test/1.mp3", "/test/2.mp3"]
        )

        self.assertEqual(len(songs_without), 2)
        titles = [s.title for s in songs_without]
        self.assertIn("Song 1", titles)
        self.assertIn("Song 2", titles)
        self.assertNotIn("Song 3", titles)

    def test_get_indexing_stats(self):
        song1 = Song(
            id=0,
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        song2 = Song(
            id=0,
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            last_modified=0.0,
            duration=200,
        )
        song3 = Song(
            id=0,
            file_path="/test/3.mp3",
            title="Song 3",
            artist="Artist 3",
            album="Album 3",
            genre="Jazz",
            last_modified=0.0,
            duration=210,
        )
        features = Features(
            song_id=0, feature_vector=np.array([1.0, 2.0], dtype=np.float32), bpm=120.0
        )

        self.db.add_song(song1, features)
        self.db.add_song(song2, features)
        self.db.add_song(song3)

        stats = self.db.get_indexing_stats()

        self.assertEqual(stats["total_songs"], 3)
        self.assertEqual(stats["songs_with_features"], 2)
        self.assertEqual(stats["songs_without_features"], 1)

    def test_get_indexing_stats_empty(self):
        stats = self.db.get_indexing_stats()

        self.assertEqual(stats["total_songs"], 0)
        self.assertEqual(stats["songs_with_features"], 0)
        self.assertEqual(stats["songs_without_features"], 0)


if __name__ == "__main__":
    unittest.main()
