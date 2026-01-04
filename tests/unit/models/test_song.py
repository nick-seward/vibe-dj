import unittest

from vibe_dj.models.song import Song


class TestSong(unittest.TestCase):
    """Test suite for Song class."""

    def test_song_creation(self):
        """Test creating a Song instance."""
        song = Song(
            id=1,
            file_path="/path/to/song.mp3",
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            genre="Rock",
            last_modified=1234567890.0,
            duration=180,
        )

        self.assertEqual(song.id, 1)
        self.assertEqual(song.title, "Test Song")
        self.assertEqual(song.artist, "Test Artist")
        self.assertEqual(song.duration, 180)

    def test_song_str(self):
        song = Song(
            id=1,
            file_path="/path/to/song.mp3",
            title="Test Song",
            artist="Test Artist",
            album="Test Album",
            genre="Rock",
            last_modified=1234567890.0,
            duration=180,
        )

        self.assertEqual(str(song), "Test Artist - Test Song")

    def test_song_with_none_values(self):
        song = Song(
            id=1,
            file_path="/path/to/song.mp3",
            title="Test Song",
            artist="Test Artist",
            album="Unknown",
            genre="Unknown",
            last_modified=1234567890.0,
            duration=None,
        )

        self.assertIsNone(song.duration)


if __name__ == "__main__":
    unittest.main()
