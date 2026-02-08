import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from vibe_dj.core.analyzer import AudioAnalyzer
from vibe_dj.core.database import MusicDatabase
from vibe_dj.core.indexer import LibraryIndexer
from vibe_dj.core.similarity import SimilarityIndex
from vibe_dj.models import Config, Features, Song


class TestLibraryIndexer:
    """Test suite for LibraryIndexer."""

    @pytest.fixture()
    def indexer_env(self):
        """Set up test fixtures with mocked dependencies before each test method."""
        config = Config()
        mock_db = MagicMock(spec=MusicDatabase)
        mock_analyzer = MagicMock(spec=AudioAnalyzer)
        mock_similarity = MagicMock(spec=SimilarityIndex)

        indexer = LibraryIndexer(config, mock_db, mock_analyzer, mock_similarity)

        return indexer, mock_db, mock_analyzer, mock_similarity

    def test_scan_files(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "song1.mp3").touch()
            Path(tmpdir, "song2.flac").touch()
            Path(tmpdir, "song3.wav").touch()
            Path(tmpdir, "readme.txt").touch()

            files = indexer.scan_files(tmpdir)

            assert len(files) == 3
            assert all(f.endswith((".mp3", ".flac", ".wav")) for f in files)

    def test_get_files_to_process_new_files(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        mock_db.get_all_file_paths_with_mtime.return_value = {}

        files = ["/path/song1.mp3", "/path/song2.mp3"]
        to_process = indexer.get_files_to_process(files)

        assert len(to_process) == 2

    def test_get_files_to_process_modified_files(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir, "song.mp3")
            test_file.touch()

            old_mtime = os.path.getmtime(str(test_file)) - 1000
            mock_db.get_all_file_paths_with_mtime.return_value = {
                str(test_file): old_mtime
            }

            to_process = indexer.get_files_to_process([str(test_file)])

            assert len(to_process) == 1

    def test_extract_metadata_phase(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        mock_analyzer.extract_metadata.return_value = (
            "Title",
            "Artist",
            "Album",
            "Rock",
        )
        mock_analyzer.get_duration.return_value = 180

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir, "song.mp3")
            test_file.touch()

            count = indexer.extract_metadata_phase([str(test_file)])

            assert count == 1
            mock_db.add_song.assert_called()
            mock_db.commit.assert_called()

    def test_extract_metadata_phase_with_callback(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        mock_analyzer.extract_metadata.return_value = (
            "Title",
            "Artist",
            "Album",
            "Rock",
        )
        mock_analyzer.get_duration.return_value = 180

        callback = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            files = []
            for i in range(3):
                f = Path(tmpdir, f"song{i}.mp3")
                f.touch()
                files.append(str(f))

            count = indexer.extract_metadata_phase(
                files, progress_callback=callback
            )

            assert count == 3
            assert callback.call_count == 3
            callback.assert_any_call("metadata", 1, 3)
            callback.assert_any_call("metadata", 2, 3)
            callback.assert_any_call("metadata", 3, 3)

    def test_extract_features_phase(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        song1 = Song(
            id=1,
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        song2 = Song(
            id=2,
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            last_modified=0.0,
            duration=200,
        )

        mock_db.get_songs_without_features.return_value = [song1, song2]

        features = Features(
            song_id=0,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0,
        )

        mock_analyzer.extract_features.return_value = features
        mock_db.get_song_by_path.return_value = song1

        count = indexer.extract_features_phase()

        assert count == 2
        mock_db.get_songs_without_features.assert_called_once()

    def test_extract_features_phase_with_callback(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        song1 = Song(
            id=1,
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        song2 = Song(
            id=2,
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            last_modified=0.0,
            duration=200,
        )

        mock_db.get_songs_without_features.return_value = [song1, song2]

        features = Features(
            song_id=0,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0,
        )

        mock_analyzer.extract_features.return_value = features
        mock_db.get_song_by_path.return_value = song1

        callback = MagicMock()
        count = indexer.extract_features_phase(progress_callback=callback)

        assert count == 2
        assert callback.call_count == 2
        # Verify callback was called with "features" phase and correct total
        for c in callback.call_args_list:
            assert c[0][0] == "features"
            assert c[0][2] == 2

    def test_extract_features_phase_no_songs(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        mock_db.get_songs_without_features.return_value = []

        count = indexer.extract_features_phase()

        assert count == 0

    def test_clean_deleted_files(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        mock_db.get_all_file_paths_with_mtime.return_value = {
            "/test/song1.mp3": 0.0,
            "/test/song2.mp3": 0.0,
            "/test/song3.mp3": 0.0,
        }

        scanned_files = ["/test/song1.mp3", "/test/song2.mp3"]

        deleted = indexer.clean_deleted_files(scanned_files)

        assert deleted == 1
        mock_db.delete_song.assert_called_once_with("/test/song3.mp3")

    def test_rebuild_similarity_index(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        song1 = Song(
            id=1,
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        features1 = Features(
            song_id=1,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0,
        )

        song2 = Song(
            id=2,
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            last_modified=0.0,
            duration=200,
        )
        features2 = Features(
            song_id=2,
            feature_vector=np.array([4.0, 5.0, 6.0], dtype=np.float32),
            bpm=130.0,
        )

        mock_db.get_all_songs_with_features.return_value = [
            (song1, features1),
            (song2, features2),
        ]

        indexer.rebuild_similarity_index()

        mock_similarity.build_index.assert_called_once()
        mock_similarity.save.assert_called_once()

    def test_rebuild_similarity_index_no_songs(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        mock_db.get_all_songs_with_features.return_value = []

        indexer.rebuild_similarity_index()

        mock_similarity.build_index.assert_not_called()

    def test_update_similarity_index_incremental_no_index(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        mock_db.get_indexing_stats.return_value = {
            "total_songs": 10,
            "songs_with_features": 10,
            "songs_without_features": 0,
        }

        with patch("os.path.exists", return_value=False):
            indexer.update_similarity_index_incremental(5)

        mock_db.get_all_songs_with_features.assert_called()
        mock_similarity.build_index.assert_called()

    def test_update_similarity_index_incremental_small_update(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        mock_db.get_indexing_stats.return_value = {
            "total_songs": 105,
            "songs_with_features": 105,
            "songs_without_features": 0,
        }

        mock_similarity.size = 100

        song = Song(
            id=101,
            file_path="/test/101.mp3",
            title="Song 101",
            artist="Artist",
            album="Album",
            genre="Rock",
            last_modified=0.0,
            duration=180,
        )
        features = Features(
            song_id=101,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0,
        )

        mock_db.get_all_songs_with_features.return_value = [(song, features)]

        with patch("os.path.exists", return_value=True):
            indexer.update_similarity_index_incremental(5)

        mock_similarity.load.assert_called()
        mock_similarity.add_vectors.assert_called()

    def test_update_similarity_index_incremental_large_update(self, indexer_env):
        indexer, mock_db, mock_analyzer, mock_similarity = indexer_env
        mock_db.get_indexing_stats.return_value = {
            "total_songs": 120,
            "songs_with_features": 120,
            "songs_without_features": 0,
        }

        mock_similarity.size = 100

        with patch("os.path.exists", return_value=True):
            indexer.update_similarity_index_incremental(20)

        mock_similarity.load.assert_called()
        mock_db.get_all_songs_with_features.assert_called()
        mock_similarity.build_index.assert_called()
