import unittest
from datetime import datetime
from vibe_dj.models.playlist import Playlist
from vibe_dj.models.song import Song


class TestPlaylist(unittest.TestCase):
    def setUp(self):
        self.song1 = Song(
            id=1, file_path="/path/1.mp3", title="Song 1", artist="Artist 1",
            genre="Rock", last_modified=0.0, duration=180
        )
        self.song2 = Song(
            id=2, file_path="/path/2.mp3", title="Song 2", artist="Artist 2",
            genre="Pop", last_modified=0.0, duration=200
        )

    def test_playlist_creation(self):
        playlist = Playlist()
        
        self.assertEqual(len(playlist), 0)
        self.assertEqual(len(playlist.songs), 0)
        self.assertEqual(len(playlist.seed_songs), 0)
        self.assertIsInstance(playlist.created_at, datetime)

    def test_add_song(self):
        playlist = Playlist()
        playlist.add_song(self.song1)
        
        self.assertEqual(len(playlist), 1)
        self.assertEqual(playlist.songs[0], self.song1)

    def test_add_multiple_songs(self):
        playlist = Playlist()
        playlist.add_song(self.song1)
        playlist.add_song(self.song2)
        
        self.assertEqual(len(playlist), 2)
        self.assertEqual(playlist.songs[0], self.song1)
        self.assertEqual(playlist.songs[1], self.song2)

    def test_remove_song(self):
        playlist = Playlist(songs=[self.song1, self.song2])
        
        result = playlist.remove_song(1)
        
        self.assertTrue(result)
        self.assertEqual(len(playlist), 1)
        self.assertEqual(playlist.songs[0], self.song2)

    def test_remove_nonexistent_song(self):
        playlist = Playlist(songs=[self.song1])
        
        result = playlist.remove_song(999)
        
        self.assertFalse(result)
        self.assertEqual(len(playlist), 1)

    def test_get_song_ids(self):
        playlist = Playlist(songs=[self.song1, self.song2])
        
        song_ids = playlist.get_song_ids()
        
        self.assertEqual(song_ids, [1, 2])

    def test_playlist_with_seeds(self):
        playlist = Playlist(songs=[self.song2], seed_songs=[self.song1])
        
        self.assertEqual(len(playlist.songs), 1)
        self.assertEqual(len(playlist.seed_songs), 1)
        self.assertEqual(playlist.seed_songs[0], self.song1)


if __name__ == "__main__":
    unittest.main()
