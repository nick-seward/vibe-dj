import tempfile
from pathlib import Path

import numpy as np
import pytest
from sqlalchemy import text

from vibe_dj.core.database import MusicDatabase
from vibe_dj.models import Config, Features, Song


def create_test_song(
    file_path: str = "/test/song.mp3",
    title: str = "Test Song",
    artist: str = "Test Artist",
    album: str = "Test Album",
    genre: str = "Rock",
    last_modified: float = 1234567890.0,
    duration: int = 180,
) -> Song:
    """Helper to create a test Song object."""
    return Song(
        file_path=file_path,
        title=title,
        artist=artist,
        album=album,
        genre=genre,
        last_modified=last_modified,
        duration=duration,
    )


def create_test_features(
    feature_vector: np.ndarray = None,
    bpm: float = 120.5,
) -> Features:
    """Helper to create a test Features object."""
    if feature_vector is None:
        feature_vector = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
    features = Features()
    features.feature_vector = feature_vector
    features.bpm = bpm
    return features


class TestMusicDatabase:
    """Test suite for MusicDatabase."""

    @pytest.fixture()
    def db_env(self):
        """Set up test fixtures with temporary database before each test method."""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        temp_db.close()

        config = Config(database_path=temp_db.name)
        db = MusicDatabase(config)
        db.connect()
        db.init_db()

        test_song = create_test_song()
        test_features = create_test_features()

        yield config, db, test_song, test_features

        db.close()
        Path(temp_db.name).unlink(missing_ok=True)

    def test_context_manager(self, db_env):
        """Test database context manager functionality."""
        config, db, test_song, test_features = db_env
        with MusicDatabase(config) as ctx_db:
            ctx_db.init_db()
            assert ctx_db.connection is not None

    def test_init_db(self, db_env):
        """Test database schema initialization."""
        config, db, test_song, test_features = db_env
        result = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = [row[0] for row in result.fetchall()]

        assert "songs" in tables
        assert "features" in tables

    def test_add_song_without_features(self, db_env):
        """Test adding a song without features."""
        config, db, test_song, test_features = db_env
        song_id = db.add_song(test_song)

        assert isinstance(song_id, int)
        assert song_id > 0

        retrieved = db.get_song(song_id)
        assert retrieved is not None
        assert retrieved.title == "Test Song"
        assert retrieved.artist == "Test Artist"

    def test_add_song_with_features(self, db_env):
        """Test adding a song with features."""
        config, db, test_song, test_features = db_env
        song_id = db.add_song(test_song, test_features)

        retrieved_song = db.get_song(song_id)
        retrieved_features = db.get_features(song_id)

        assert retrieved_song is not None
        assert retrieved_features is not None
        assert retrieved_features.bpm == 120.5
        np.testing.assert_array_almost_equal(
            retrieved_features.feature_vector, test_features.feature_vector
        )

    def test_get_song_by_path(self, db_env):
        """Test retrieving a song by its file path."""
        config, db, test_song, test_features = db_env
        song_id = db.add_song(test_song)

        retrieved = db.get_song_by_path("/test/song.mp3")

        assert retrieved is not None
        assert retrieved.title == "Test Song"

    def test_find_songs_by_title(self, db_env):
        """Test finding songs by partial title match."""
        config, db, test_song, test_features = db_env
        song1 = create_test_song(
            file_path="/test/1.mp3",
            title="Rock Song",
            artist="Artist 1",
            album="Album 1",
        )
        song2 = create_test_song(
            file_path="/test/2.mp3",
            title="Another Rock Track",
            artist="Artist 2",
            album="Album 2",
            duration=200,
        )
        song3 = create_test_song(
            file_path="/test/3.mp3",
            title="Pop Song",
            artist="Artist 3",
            album="Album 3",
            genre="Pop",
            duration=190,
        )

        db.add_song(song1)
        db.add_song(song2)
        db.add_song(song3)

        results = db.find_songs_by_title("Rock")

        assert len(results) == 2
        titles = [s.title for s in results]
        assert "Rock Song" in titles
        assert "Another Rock Track" in titles

    def test_find_song_exact(self, db_env):
        config, db, test_song, test_features = db_env
        song1 = create_test_song(
            file_path="/test/1.mp3",
            title="Test Song",
            artist="Artist 1",
            album="Album 1",
        )
        song2 = create_test_song(
            file_path="/test/2.mp3",
            title="Test Song",
            artist="Artist 2",
            album="Album 2",
            duration=200,
        )

        db.add_song(song1)
        db.add_song(song2)

        result = db.find_song_exact("Test Song", "Artist 1", "Album 1")

        assert result is not None
        assert result.title == "Test Song"
        assert result.artist == "Artist 1"
        assert result.album == "Album 1"

    def test_find_song_exact_no_match(self, db_env):
        config, db, test_song, test_features = db_env
        song1 = create_test_song(
            file_path="/test/1.mp3",
            title="Test Song",
            artist="Artist 1",
            album="Album 1",
        )

        db.add_song(song1)

        result = db.find_song_exact("Test Song", "Wrong Artist", "Album 1")

        assert result is None

    def test_get_song_with_features(self, db_env):
        config, db, test_song, test_features = db_env
        song_id = db.add_song(test_song, test_features)

        result = db.get_song_with_features(song_id)

        assert result is not None
        song, features = result
        assert song.title == "Test Song"
        assert features.bpm == 120.5

    def test_get_all_songs_with_features(self, db_env):
        config, db, test_song, test_features = db_env
        song1 = create_test_song(
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
        )
        features1 = create_test_features(
            feature_vector=np.array([1.0, 2.0], dtype=np.float32), bpm=120.0
        )

        song2 = create_test_song(
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            duration=200,
        )
        features2 = create_test_features(
            feature_vector=np.array([3.0, 4.0], dtype=np.float32), bpm=130.0
        )

        db.add_song(song1, features1)
        db.add_song(song2, features2)

        results = db.get_all_songs_with_features()

        assert len(results) == 2
        assert results[0][0].title == "Song 1"
        assert results[1][0].title == "Song 2"

    def test_delete_song(self, db_env):
        config, db, test_song, test_features = db_env
        song_id = db.add_song(test_song)

        result = db.delete_song("/test/song.mp3")

        assert result
        assert db.get_song(song_id) is None

    def test_delete_nonexistent_song(self, db_env):
        config, db, test_song, test_features = db_env
        result = db.delete_song("/nonexistent/song.mp3")

        assert not result

    def test_get_songs_by_ids(self, db_env):
        config, db, test_song, test_features = db_env
        song1 = create_test_song(
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
        )
        song2 = create_test_song(
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            duration=200,
        )

        id1 = db.add_song(song1)
        id2 = db.add_song(song2)

        results = db.get_songs_by_ids([id1, id2])

        assert len(results) == 2
        titles = [s.title for s in results]
        assert "Song 1" in titles
        assert "Song 2" in titles

    def test_get_all_file_paths_with_mtime(self, db_env):
        config, db, test_song, test_features = db_env
        db.add_song(test_song)

        paths = db.get_all_file_paths_with_mtime()

        assert "/test/song.mp3" in paths
        assert paths["/test/song.mp3"] == 1234567890.0

    def test_get_songs_without_features(self, db_env):
        config, db, test_song, test_features = db_env
        song1 = create_test_song(
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
        )
        song2 = create_test_song(
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            duration=200,
        )
        features = create_test_features(
            feature_vector=np.array([1.0, 2.0], dtype=np.float32), bpm=120.0
        )

        db.add_song(song1, features)
        db.add_song(song2)

        songs_without = db.get_songs_without_features()

        assert len(songs_without) == 1
        assert songs_without[0].title == "Song 2"

    def test_get_songs_without_features_filtered(self, db_env):
        config, db, test_song, test_features = db_env
        song1 = create_test_song(
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
        )
        song2 = create_test_song(
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            duration=200,
        )
        song3 = create_test_song(
            file_path="/test/3.mp3",
            title="Song 3",
            artist="Artist 3",
            album="Album 3",
            genre="Jazz",
            duration=210,
        )

        db.add_song(song1)
        db.add_song(song2)
        db.add_song(song3)

        songs_without = db.get_songs_without_features(
            ["/test/1.mp3", "/test/2.mp3"]
        )

        assert len(songs_without) == 2
        titles = [s.title for s in songs_without]
        assert "Song 1" in titles
        assert "Song 2" in titles
        assert "Song 3" not in titles

    def test_get_library_stats(self, db_env):
        """Test comprehensive library statistics."""
        config, db, test_song, test_features = db_env
        song1 = create_test_song(
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist A",
            album="Album X",
            duration=180,
        )
        song2 = create_test_song(
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist A",
            album="Album Y",
            genre="Pop",
            duration=200,
        )
        song3 = create_test_song(
            file_path="/test/3.mp3",
            title="Song 3",
            artist="Artist B",
            album="Album X",
            genre="Jazz",
            duration=210,
        )
        features1 = create_test_features(
            feature_vector=np.array([1.0, 2.0], dtype=np.float32), bpm=120.0
        )
        features2 = create_test_features(
            feature_vector=np.array([3.0, 4.0], dtype=np.float32), bpm=130.0
        )

        db.add_song(song1, features1)
        db.add_song(song2, features2)
        db.add_song(song3)

        stats = db.get_library_stats()

        assert stats["total_songs"] == 3
        assert stats["artist_count"] == 2  # Artist A, Artist B
        assert stats["album_count"] == 2  # Album X, Album Y
        assert stats["total_duration"] == 590  # 180 + 200 + 210
        assert stats["songs_with_features"] == 2
        assert stats["last_indexed"] is not None

    def test_get_library_stats_empty(self, db_env):
        """Test library statistics on empty database."""
        config, db, test_song, test_features = db_env
        stats = db.get_library_stats()

        assert stats["total_songs"] == 0
        assert stats["artist_count"] == 0
        assert stats["album_count"] == 0
        assert stats["total_duration"] == 0
        assert stats["songs_with_features"] == 0
        assert stats["last_indexed"] is None

    def test_get_library_stats_null_durations(self, db_env):
        """Test library statistics when some songs have null duration."""
        config, db, test_song, test_features = db_env
        song1 = create_test_song(
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist A",
            album="Album X",
            duration=180,
        )
        song2 = Song(
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist B",
            album="Album Y",
            genre="Pop",
            last_modified=1234567891.0,
            duration=None,
        )

        db.add_song(song1)
        db.add_song(song2)

        stats = db.get_library_stats()

        assert stats["total_songs"] == 2
        assert stats["total_duration"] == 180

    def test_get_indexing_stats(self, db_env):
        config, db, test_song, test_features = db_env
        song1 = create_test_song(
            file_path="/test/1.mp3",
            title="Song 1",
            artist="Artist 1",
            album="Album 1",
        )
        song2 = create_test_song(
            file_path="/test/2.mp3",
            title="Song 2",
            artist="Artist 2",
            album="Album 2",
            genre="Pop",
            duration=200,
        )
        song3 = create_test_song(
            file_path="/test/3.mp3",
            title="Song 3",
            artist="Artist 3",
            album="Album 3",
            genre="Jazz",
            duration=210,
        )
        features1 = create_test_features(
            feature_vector=np.array([1.0, 2.0], dtype=np.float32), bpm=120.0
        )
        features2 = create_test_features(
            feature_vector=np.array([1.0, 2.0], dtype=np.float32), bpm=120.0
        )

        db.add_song(song1, features1)
        db.add_song(song2, features2)
        db.add_song(song3)

        stats = db.get_indexing_stats()

        assert stats["total_songs"] == 3
        assert stats["songs_with_features"] == 2
        assert stats["songs_without_features"] == 1

    def test_get_indexing_stats_empty(self, db_env):
        config, db, test_song, test_features = db_env
        stats = db.get_indexing_stats()

        assert stats["total_songs"] == 0
        assert stats["songs_with_features"] == 0
        assert stats["songs_without_features"] == 0
