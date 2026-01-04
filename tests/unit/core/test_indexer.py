import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import numpy as np

from vibe_dj.core.analyzer import AudioAnalyzer
from vibe_dj.core.database import MusicDatabase
from vibe_dj.core.indexer import LibraryIndexer
from vibe_dj.core.similarity import SimilarityIndex
from vibe_dj.models import Config, Features, Song


class TestLibraryIndexer(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.mock_db = MagicMock(spec=MusicDatabase)
        self.mock_analyzer = MagicMock(spec=AudioAnalyzer)
        self.mock_similarity = MagicMock(spec=SimilarityIndex)
        
        self.indexer = LibraryIndexer(
            self.config,
            self.mock_db,
            self.mock_analyzer,
            self.mock_similarity
        )

    def test_scan_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "song1.mp3").touch()
            Path(tmpdir, "song2.flac").touch()
            Path(tmpdir, "song3.wav").touch()
            Path(tmpdir, "readme.txt").touch()
            
            files = self.indexer.scan_files(tmpdir)
            
            self.assertEqual(len(files), 3)
            self.assertTrue(all(f.endswith(('.mp3', '.flac', '.wav')) for f in files))

    def test_get_files_to_process_new_files(self):
        self.mock_db.get_all_file_paths_with_mtime.return_value = {}
        
        files = ["/path/song1.mp3", "/path/song2.mp3"]
        to_process = self.indexer.get_files_to_process(files)
        
        self.assertEqual(len(to_process), 2)

    def test_get_files_to_process_modified_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir, "song.mp3")
            test_file.touch()
            
            old_mtime = os.path.getmtime(str(test_file)) - 1000
            self.mock_db.get_all_file_paths_with_mtime.return_value = {
                str(test_file): old_mtime
            }
            
            to_process = self.indexer.get_files_to_process([str(test_file)])
            
            self.assertEqual(len(to_process), 1)

    def test_extract_metadata_phase(self):
        self.mock_analyzer.extract_metadata.return_value = ("Title", "Artist", "Album", "Rock")
        self.mock_analyzer.get_duration.return_value = 180
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir, "song.mp3")
            test_file.touch()
            
            count = self.indexer.extract_metadata_phase([str(test_file)])
            
            self.assertEqual(count, 1)
            self.mock_db.add_song.assert_called()
            self.mock_db.commit.assert_called()

    def test_extract_features_phase(self):
        song1 = Song(
            id=1, file_path="/test/1.mp3", title="Song 1", artist="Artist 1",
            album="Album 1", genre="Rock", last_modified=0.0, duration=180
        )
        song2 = Song(
            id=2, file_path="/test/2.mp3", title="Song 2", artist="Artist 2",
            album="Album 2", genre="Pop", last_modified=0.0, duration=200
        )
        
        self.mock_db.get_songs_without_features.return_value = [song1, song2]
        
        features = Features(
            song_id=0,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0
        )
        
        self.mock_analyzer.extract_features.return_value = features
        self.mock_db.get_song_by_path.return_value = song1
        
        count = self.indexer.extract_features_phase()
        
        self.assertEqual(count, 2)
        self.mock_db.get_songs_without_features.assert_called_once()

    def test_extract_features_phase_no_songs(self):
        self.mock_db.get_songs_without_features.return_value = []
        
        count = self.indexer.extract_features_phase()
        
        self.assertEqual(count, 0)

    def test_clean_deleted_files(self):
        self.mock_db.get_all_file_paths_with_mtime.return_value = {
            "/test/song1.mp3": 0.0,
            "/test/song2.mp3": 0.0,
            "/test/song3.mp3": 0.0
        }
        
        scanned_files = ["/test/song1.mp3", "/test/song2.mp3"]
        
        deleted = self.indexer.clean_deleted_files(scanned_files)
        
        self.assertEqual(deleted, 1)
        self.mock_db.delete_song.assert_called_once_with("/test/song3.mp3")

    def test_rebuild_similarity_index(self):
        song1 = Song(
            id=1, file_path="/test/1.mp3", title="Song 1", artist="Artist 1",
            album="Album 1", genre="Rock", last_modified=0.0, duration=180
        )
        features1 = Features(
            song_id=1,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0
        )
        
        song2 = Song(
            id=2, file_path="/test/2.mp3", title="Song 2", artist="Artist 2",
            album="Album 2", genre="Pop", last_modified=0.0, duration=200
        )
        features2 = Features(
            song_id=2,
            feature_vector=np.array([4.0, 5.0, 6.0], dtype=np.float32),
            bpm=130.0
        )
        
        self.mock_db.get_all_songs_with_features.return_value = [
            (song1, features1),
            (song2, features2)
        ]
        
        self.indexer.rebuild_similarity_index()
        
        self.mock_similarity.build_index.assert_called_once()
        self.mock_similarity.save.assert_called_once()

    def test_rebuild_similarity_index_no_songs(self):
        self.mock_db.get_all_songs_with_features.return_value = []
        
        self.indexer.rebuild_similarity_index()
        
        self.mock_similarity.build_index.assert_not_called()

    def test_update_similarity_index_incremental_no_index(self):
        self.mock_db.get_indexing_stats.return_value = {
            'total_songs': 10,
            'songs_with_features': 10,
            'songs_without_features': 0
        }
        
        with patch('os.path.exists', return_value=False):
            self.indexer.update_similarity_index_incremental(5)
        
        self.mock_db.get_all_songs_with_features.assert_called()
        self.mock_similarity.build_index.assert_called()

    def test_update_similarity_index_incremental_small_update(self):
        self.mock_db.get_indexing_stats.return_value = {
            'total_songs': 105,
            'songs_with_features': 105,
            'songs_without_features': 0
        }
        
        self.mock_similarity.size = 100
        
        song = Song(
            id=101, file_path="/test/101.mp3", title="Song 101", artist="Artist",
            album="Album", genre="Rock", last_modified=0.0, duration=180
        )
        features = Features(
            song_id=101,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0
        )
        
        self.mock_db.get_all_songs_with_features.return_value = [(song, features)]
        
        with patch('os.path.exists', return_value=True):
            self.indexer.update_similarity_index_incremental(5)
        
        self.mock_similarity.load.assert_called()
        self.mock_similarity.add_vectors.assert_called()

    def test_update_similarity_index_incremental_large_update(self):
        self.mock_db.get_indexing_stats.return_value = {
            'total_songs': 120,
            'songs_with_features': 120,
            'songs_without_features': 0
        }
        
        self.mock_similarity.size = 100
        
        with patch('os.path.exists', return_value=True):
            self.indexer.update_similarity_index_incremental(20)
        
        self.mock_similarity.load.assert_called()
        self.mock_db.get_all_songs_with_features.assert_called()
        self.mock_similarity.build_index.assert_called()


if __name__ == "__main__":
    unittest.main()
