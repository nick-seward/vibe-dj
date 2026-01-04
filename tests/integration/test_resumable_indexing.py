"""Integration test for resumable indexing functionality."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np

from vibe_dj.core.analyzer import AudioAnalyzer
from vibe_dj.core.database import MusicDatabase
from vibe_dj.core.indexer import LibraryIndexer
from vibe_dj.core.similarity import SimilarityIndex
from vibe_dj.models import Config


class TestResumableIndexing(unittest.TestCase):
    """Test that indexing can be resumed after interruption."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.music_dir = os.path.join(self.temp_dir, "music")
        os.makedirs(self.music_dir)
        
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.index_path = os.path.join(self.temp_dir, "test_index.bin")
        
        self.config = Config(
            database_path=self.db_path,
            faiss_index_path=self.index_path,
            batch_size=2,
            parallel_workers=2
        )
        
        self._create_test_audio_files()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_test_audio_files(self):
        """Create dummy audio files for testing."""
        for i in range(5):
            file_path = os.path.join(self.music_dir, f"song{i}.mp3")
            Path(file_path).touch()
    
    def test_resume_after_phase1_interruption(self):
        """Test that indexing can resume after Phase 1 (metadata) is interrupted."""
        with MusicDatabase(self.config) as db:
            db.init_db()
            analyzer = AudioAnalyzer(self.config)
            similarity_index = SimilarityIndex(self.config)
            indexer = LibraryIndexer(self.config, db, analyzer, similarity_index)
            
            all_files = indexer.scan_files(self.music_dir)
            files_to_process = indexer.get_files_to_process(all_files)
            
            self.assertEqual(len(files_to_process), 5)
            
            metadata_count = indexer.extract_metadata_phase(files_to_process[:3])
            self.assertEqual(metadata_count, 3)
            
            stats = db.get_indexing_stats()
            self.assertEqual(stats['total_songs'], 3)
            self.assertEqual(stats['songs_without_features'], 3)
        
        with MusicDatabase(self.config) as db:
            analyzer = AudioAnalyzer(self.config)
            similarity_index = SimilarityIndex(self.config)
            indexer = LibraryIndexer(self.config, db, analyzer, similarity_index)
            
            all_files = indexer.scan_files(self.music_dir)
            files_to_process = indexer.get_files_to_process(all_files)
            
            self.assertEqual(len(files_to_process), 2)
            
            metadata_count = indexer.extract_metadata_phase(files_to_process)
            self.assertEqual(metadata_count, 2)
            
            stats = db.get_indexing_stats()
            self.assertEqual(stats['total_songs'], 5)
            self.assertEqual(stats['songs_without_features'], 5)
    
    def test_resume_after_phase2_interruption(self):
        """Test that indexing can resume after Phase 2 (features) is interrupted."""
        with MusicDatabase(self.config) as db:
            db.init_db()
            analyzer = AudioAnalyzer(self.config)
            similarity_index = SimilarityIndex(self.config)
            indexer = LibraryIndexer(self.config, db, analyzer, similarity_index)
            
            all_files = indexer.scan_files(self.music_dir)
            files_to_process = indexer.get_files_to_process(all_files)
            
            metadata_count = indexer.extract_metadata_phase(files_to_process)
            self.assertEqual(metadata_count, 5)
            
            stats_before = db.get_indexing_stats()
            self.assertEqual(stats_before['total_songs'], 5)
            self.assertEqual(stats_before['songs_without_features'], 5)
        
        with MusicDatabase(self.config) as db:
            stats = db.get_indexing_stats()
            self.assertEqual(stats['total_songs'], 5)
            self.assertEqual(stats['songs_without_features'], 5)
            
            songs_without = db.get_songs_without_features()
            self.assertEqual(len(songs_without), 5)
    
    def test_no_duplicate_processing(self):
        """Test that files are not processed twice."""
        with MusicDatabase(self.config) as db:
            db.init_db()
            analyzer = AudioAnalyzer(self.config)
            similarity_index = SimilarityIndex(self.config)
            indexer = LibraryIndexer(self.config, db, analyzer, similarity_index)
            
            all_files = indexer.scan_files(self.music_dir)
            files_to_process = indexer.get_files_to_process(all_files)
            self.assertEqual(len(files_to_process), 5)
            
            metadata_count = indexer.extract_metadata_phase(files_to_process)
            self.assertEqual(metadata_count, 5)
        
        with MusicDatabase(self.config) as db:
            analyzer = AudioAnalyzer(self.config)
            similarity_index = SimilarityIndex(self.config)
            indexer = LibraryIndexer(self.config, db, analyzer, similarity_index)
            
            all_files = indexer.scan_files(self.music_dir)
            files_to_process = indexer.get_files_to_process(all_files)
            
            self.assertEqual(len(files_to_process), 0)
            
            stats = db.get_indexing_stats()
            self.assertEqual(stats['total_songs'], 5)


if __name__ == "__main__":
    unittest.main()
