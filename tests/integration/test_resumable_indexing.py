"""Integration test for resumable indexing functionality."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from vibe_dj.core.analyzer import AudioAnalyzer
from vibe_dj.core.database import MusicDatabase
from vibe_dj.core.indexer import LibraryIndexer
from vibe_dj.core.similarity import SimilarityIndex
from vibe_dj.models import Config


@pytest.fixture()
def indexing_env():
    """Set up temp dirs, config, and dummy audio files; clean up after test."""
    temp_dir = tempfile.mkdtemp()
    music_dir = os.path.join(temp_dir, "music")
    os.makedirs(music_dir)

    db_path = os.path.join(temp_dir, "test.db")
    index_path = os.path.join(temp_dir, "test_index.bin")

    config = Config(
        database_path=db_path,
        faiss_index_path=index_path,
        batch_size=2,
        parallel_workers=2,
    )

    for i in range(5):
        file_path = os.path.join(music_dir, f"song{i}.mp3")
        Path(file_path).touch()

    yield config, music_dir

    shutil.rmtree(temp_dir, ignore_errors=True)


def test_resume_after_phase1_interruption(indexing_env):
    """Test that indexing can resume after Phase 1 (metadata) is interrupted."""
    config, music_dir = indexing_env

    with MusicDatabase(config) as db:
        db.init_db()
        analyzer = AudioAnalyzer(config)
        similarity_index = SimilarityIndex(config)
        indexer = LibraryIndexer(config, db, analyzer, similarity_index)

        all_files = indexer.scan_files(music_dir)
        files_to_process = indexer.get_files_to_process(all_files)

        assert len(files_to_process) == 5

        metadata_count = indexer.extract_metadata_phase(files_to_process[:3])
        assert metadata_count == 3

        stats = db.get_indexing_stats()
        assert stats["total_songs"] == 3
        assert stats["songs_without_features"] == 3

    with MusicDatabase(config) as db:
        analyzer = AudioAnalyzer(config)
        similarity_index = SimilarityIndex(config)
        indexer = LibraryIndexer(config, db, analyzer, similarity_index)

        all_files = indexer.scan_files(music_dir)
        files_to_process = indexer.get_files_to_process(all_files)

        assert len(files_to_process) == 2

        metadata_count = indexer.extract_metadata_phase(files_to_process)
        assert metadata_count == 2

        stats = db.get_indexing_stats()
        assert stats["total_songs"] == 5
        assert stats["songs_without_features"] == 5


def test_resume_after_phase2_interruption(indexing_env):
    """Test that indexing can resume after Phase 2 (features) is interrupted."""
    config, music_dir = indexing_env

    with MusicDatabase(config) as db:
        db.init_db()
        analyzer = AudioAnalyzer(config)
        similarity_index = SimilarityIndex(config)
        indexer = LibraryIndexer(config, db, analyzer, similarity_index)

        all_files = indexer.scan_files(music_dir)
        files_to_process = indexer.get_files_to_process(all_files)

        metadata_count = indexer.extract_metadata_phase(files_to_process)
        assert metadata_count == 5

        stats_before = db.get_indexing_stats()
        assert stats_before["total_songs"] == 5
        assert stats_before["songs_without_features"] == 5

    with MusicDatabase(config) as db:
        stats = db.get_indexing_stats()
        assert stats["total_songs"] == 5
        assert stats["songs_without_features"] == 5

        songs_without = db.get_songs_without_features()
        assert len(songs_without) == 5


def test_no_duplicate_processing(indexing_env):
    """Test that files are not processed twice."""
    config, music_dir = indexing_env

    with MusicDatabase(config) as db:
        db.init_db()
        analyzer = AudioAnalyzer(config)
        similarity_index = SimilarityIndex(config)
        indexer = LibraryIndexer(config, db, analyzer, similarity_index)

        all_files = indexer.scan_files(music_dir)
        files_to_process = indexer.get_files_to_process(all_files)
        assert len(files_to_process) == 5

        metadata_count = indexer.extract_metadata_phase(files_to_process)
        assert metadata_count == 5

    with MusicDatabase(config) as db:
        analyzer = AudioAnalyzer(config)
        similarity_index = SimilarityIndex(config)
        indexer = LibraryIndexer(config, db, analyzer, similarity_index)

        all_files = indexer.scan_files(music_dir)
        files_to_process = indexer.get_files_to_process(all_files)

        assert len(files_to_process) == 0

        stats = db.get_indexing_stats()
        assert stats["total_songs"] == 5
