import unittest
from unittest.mock import MagicMock, patch, call
import tempfile
import os
import numpy as np
from pathlib import Path
from vibe_dj.core.indexer import LibraryIndexer
from vibe_dj.core.database import MusicDatabase
from vibe_dj.core.analyzer import AudioAnalyzer
from vibe_dj.core.similarity import SimilarityIndex
from vibe_dj.models import Config, Song, Features


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
        self.mock_analyzer.extract_metadata.return_value = ("Title", "Artist", "Rock")
        self.mock_analyzer.get_duration.return_value = 180
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir, "song.mp3")
            test_file.touch()
            
            metadata = self.indexer.extract_metadata_phase([str(test_file)])
            
            self.assertIn(str(test_file), metadata)
            self.assertEqual(metadata[str(test_file)]['title'], "Title")
            self.assertEqual(metadata[str(test_file)]['artist'], "Artist")

    def test_write_to_database(self):
        file_path = "/test/song.mp3"
        
        file_metadata = {
            file_path: {
                'title': "Test Song",
                'artist': "Test Artist",
                'genre': "Rock",
                'mtime': 1234567890.0,
                'duration': 180
            }
        }
        
        features = Features(
            song_id=0,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0
        )
        
        features_results = {
            file_path: (features, 120.0)
        }
        
        processed, failed = self.indexer.write_to_database(file_metadata, features_results)
        
        self.assertEqual(processed, 1)
        self.assertEqual(failed, 0)
        self.mock_db.add_song.assert_called_once()

    def test_write_to_database_with_failures(self):
        file_metadata = {
            "/test/song1.mp3": {'title': "Song 1", 'artist': "Artist 1", 'genre': "Rock", 
                               'mtime': 0.0, 'duration': 180},
            "/test/song2.mp3": {'title': "Song 2", 'artist': "Artist 2", 'genre': "Pop", 
                               'mtime': 0.0, 'duration': 200}
        }
        
        features = Features(
            song_id=0,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0
        )
        
        features_results = {
            "/test/song1.mp3": (features, 120.0)
        }
        
        processed, failed = self.indexer.write_to_database(file_metadata, features_results)
        
        self.assertEqual(processed, 1)
        self.assertEqual(failed, 1)

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
            genre="Rock", last_modified=0.0, duration=180
        )
        features1 = Features(
            song_id=1,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0
        )
        
        song2 = Song(
            id=2, file_path="/test/2.mp3", title="Song 2", artist="Artist 2",
            genre="Pop", last_modified=0.0, duration=200
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


if __name__ == "__main__":
    unittest.main()
