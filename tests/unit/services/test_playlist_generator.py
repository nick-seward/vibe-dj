import unittest
from unittest.mock import MagicMock
import numpy as np
from vibe_dj.services.playlist_generator import PlaylistGenerator
from vibe_dj.core.database import MusicDatabase
from vibe_dj.core.similarity import SimilarityIndex
from vibe_dj.models import Config, Song, Features


class TestPlaylistGenerator(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.mock_db = MagicMock(spec=MusicDatabase)
        self.mock_similarity = MagicMock(spec=SimilarityIndex)
        
        self.generator = PlaylistGenerator(
            self.config,
            self.mock_db,
            self.mock_similarity
        )
        
        self.test_song1 = Song(
            id=1, file_path="/test/1.mp3", title="Test Song 1", artist="Artist 1",
            album="Album 1", genre="Rock", last_modified=0.0, duration=180
        )
        self.test_song2 = Song(
            id=2, file_path="/test/2.mp3", title="Test Song 2", artist="Artist 2",
            album="Album 2", genre="Pop", last_modified=0.0, duration=200
        )
        self.test_features1 = Features(
            song_id=1,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0
        )
        self.test_features2 = Features(
            song_id=2,
            feature_vector=np.array([4.0, 5.0, 6.0], dtype=np.float32),
            bpm=130.0
        )

    def test_find_seed_songs(self):
        self.mock_db.find_song_exact.return_value = self.test_song1
        
        seeds = self.generator.find_seed_songs([{"title": "Test Song 1", "artist": "Artist 1", "album": "Album 1"}])
        
        self.assertEqual(len(seeds), 1)
        self.assertEqual(seeds[0], self.test_song1)

    def test_find_seed_songs_no_match(self):
        self.mock_db.find_song_exact.return_value = None
        
        seeds = self.generator.find_seed_songs([{"title": "Nonexistent Song", "artist": "Unknown", "album": "Unknown"}])
        
        self.assertEqual(len(seeds), 0)

    def test_get_seed_vectors(self):
        self.mock_db.get_features.return_value = self.test_features1
        
        vectors = self.generator.get_seed_vectors([self.test_song1])
        
        self.assertEqual(len(vectors), 1)
        np.testing.assert_array_equal(vectors[0], self.test_features1.feature_vector)

    def test_compute_average_vector(self):
        vectors = [
            np.array([1.0, 2.0, 3.0], dtype=np.float32),
            np.array([3.0, 4.0, 5.0], dtype=np.float32)
        ]
        
        avg = self.generator.compute_average_vector(vectors)
        
        expected = np.array([2.0, 3.0, 4.0], dtype=np.float32)
        np.testing.assert_array_almost_equal(avg, expected)

    def test_compute_average_vector_empty(self):
        with self.assertRaises(ValueError):
            self.generator.compute_average_vector([])

    def test_perturb_query_vector_with_noise(self):
        query_vector = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        
        perturbed = self.generator.perturb_query_vector(query_vector, noise_scale=0.1)
        
        self.assertEqual(perturbed.shape, query_vector.shape)
        self.assertFalse(np.array_equal(perturbed, query_vector))

    def test_perturb_query_vector_no_noise(self):
        query_vector = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        
        perturbed = self.generator.perturb_query_vector(query_vector, noise_scale=0.0)
        
        np.testing.assert_array_equal(perturbed, query_vector)

    def test_perturb_query_vector_uses_config(self):
        self.config.query_noise_scale = 0.2
        query_vector = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        
        perturbed = self.generator.perturb_query_vector(query_vector)
        
        self.assertEqual(perturbed.shape, query_vector.shape)

    def test_find_similar_songs(self):
        song3 = Song(id=3, file_path="/test/3.mp3", title="Song 3", artist="Artist 3",
                     album="Album 3", genre="Rock", last_modified=0.0, duration=190)
        song4 = Song(id=4, file_path="/test/4.mp3", title="Song 4", artist="Artist 4",
                     album="Album 4", genre="Pop", last_modified=0.0, duration=200)
        features3 = Features(song_id=3, feature_vector=np.array([7.0, 8.0, 9.0], dtype=np.float32), bpm=125.0)
        features4 = Features(song_id=4, feature_vector=np.array([10.0, 11.0, 12.0], dtype=np.float32), bpm=135.0)
        
        self.mock_similarity.search.return_value = (
            np.array([0.1, 0.2, 0.3, 0.4]),
            np.array([2, 3, 4, 5])
        )
        self.mock_db.get_song_with_features.side_effect = [
            (self.test_song2, self.test_features2),
            (song3, features3),
            (song4, features4)
        ]
        
        query = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        similar = self.generator.find_similar_songs(query, count=2, exclude_ids={1}, candidate_multiplier=1)
        
        self.assertEqual(len(similar), 2)

    def test_find_similar_songs_with_sampling(self):
        songs = []
        features = []
        for i in range(2, 10):
            song = Song(id=i, file_path=f"/test/{i}.mp3", title=f"Song {i}", 
                       artist=f"Artist {i}", album=f"Album {i}", genre="Rock", last_modified=0.0, duration=180)
            feat = Features(song_id=i, feature_vector=np.array([float(i), float(i+1), float(i+2)], dtype=np.float32), 
                          bpm=120.0 + i)
            songs.append(song)
            features.append(feat)
        
        self.mock_similarity.search.return_value = (
            np.array([0.1 * i for i in range(len(songs))]),
            np.array([s.id for s in songs])
        )
        self.mock_db.get_song_with_features.side_effect = list(zip(songs, features))
        
        query = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        similar = self.generator.find_similar_songs(query, count=2, exclude_ids={1}, candidate_multiplier=4)
        
        self.assertEqual(len(similar), 2)
        for song in similar:
            self.assertIn(song.id, [s.id for s in songs])

    def test_sort_by_bpm(self):
        song_low_bpm = Song(
            id=1, file_path="/test/1.mp3", title="Low BPM", artist="Artist 1",
            album="Album 1", genre="Rock", last_modified=0.0, duration=180
        )
        song_high_bpm = Song(
            id=2, file_path="/test/2.mp3", title="High BPM", artist="Artist 2",
            album="Album 2", genre="Rock", last_modified=0.0, duration=180
        )
        
        features_low = Features(
            song_id=1,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=100.0
        )
        features_high = Features(
            song_id=2,
            feature_vector=np.array([4.0, 5.0, 6.0], dtype=np.float32),
            bpm=150.0
        )
        
        self.mock_db.get_features.side_effect = [features_high, features_low]
        
        sorted_songs = self.generator.sort_by_bpm([song_high_bpm, song_low_bpm], bpm_jitter_percent=0.0)
        
        self.assertEqual(sorted_songs[0].id, 1)
        self.assertEqual(sorted_songs[1].id, 2)

    def test_generate_playlist(self):
        song3 = Song(id=3, file_path="/test/3.mp3", title="Song 3", artist="Artist 3",
                     album="Album 3", genre="Rock", last_modified=0.0, duration=190)
        features3 = Features(song_id=3, feature_vector=np.array([7.0, 8.0, 9.0], dtype=np.float32), bpm=125.0)
        
        self.mock_db.find_song_exact.return_value = self.test_song1
        self.mock_db.get_features.return_value = self.test_features1
        
        self.mock_similarity.search.return_value = (
            np.array([0.1, 0.2]),
            np.array([2, 3])
        )
        self.mock_db.get_song_with_features.side_effect = [
            (self.test_song2, self.test_features2),
            (song3, features3)
        ]
        
        playlist = self.generator.generate([{"title": "Test Song 1", "artist": "Artist 1", "album": "Album 1"}], length=2, candidate_multiplier=1)
        
        self.assertIsNotNone(playlist)
        self.assertEqual(len(playlist.seed_songs), 1)
        self.assertGreater(len(playlist.songs), 0)

    def test_generate_playlist_with_custom_noise(self):
        song3 = Song(id=3, file_path="/test/3.mp3", title="Song 3", artist="Artist 3",
                     album="Album 3", genre="Rock", last_modified=0.0, duration=190)
        features3 = Features(song_id=3, feature_vector=np.array([7.0, 8.0, 9.0], dtype=np.float32), bpm=125.0)
        
        self.mock_db.find_song_exact.return_value = self.test_song1
        self.mock_db.get_features.return_value = self.test_features1
        
        self.mock_similarity.search.return_value = (
            np.array([0.1, 0.2]),
            np.array([2, 3])
        )
        self.mock_db.get_song_with_features.side_effect = [
            (self.test_song2, self.test_features2),
            (song3, features3)
        ]
        
        playlist = self.generator.generate([{"title": "Test Song 1", "artist": "Artist 1", "album": "Album 1"}], length=2, 
                                          query_noise_scale=0.2, candidate_multiplier=1)
        
        self.assertIsNotNone(playlist)
        self.assertEqual(len(playlist.seed_songs), 1)
        self.assertGreater(len(playlist.songs), 0)

    def test_generate_playlist_no_seeds(self):
        with self.assertRaises(ValueError):
            self.generator.generate([])

    def test_generate_playlist_no_seed_found(self):
        self.mock_db.find_song_exact.return_value = None
        
        with self.assertRaises(ValueError):
            self.generator.generate([{"title": "Nonexistent Song", "artist": "Unknown", "album": "Unknown"}])


if __name__ == "__main__":
    unittest.main()
