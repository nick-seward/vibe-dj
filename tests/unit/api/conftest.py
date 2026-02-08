import os
import tempfile

import numpy as np
import pytest
from fastapi.testclient import TestClient

from vibe_dj.api.background import JobManager
from vibe_dj.app import app
from vibe_dj.core import MusicDatabase
from vibe_dj.models import Config, Features, Song


@pytest.fixture
def test_config():
    """Create a test configuration with in-memory database."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    config = Config(
        database_path=db_path,
        faiss_index_path="test_faiss.bin",
        parallel_workers=2,
    )

    yield config

    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def test_db(test_config):
    """Create a test database with sample data."""
    with MusicDatabase(test_config) as db:
        db.init_db()

        song1 = Song(
            id=1,
            file_path="/test/song1.mp3",
            title="Test Song 1",
            artist="Test Artist 1",
            album="Test Album 1",
            genre="Rock",
            last_modified=1234567890.0,
            duration=180,
        )
        song2 = Song(
            id=2,
            file_path="/test/song2.mp3",
            title="Test Song 2",
            artist="Test Artist 2",
            album="Test Album 2",
            genre="Pop",
            last_modified=1234567891.0,
            duration=200,
        )

        features1 = Features(
            song_id=1,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0,
        )
        features2 = Features(
            song_id=2,
            feature_vector=np.array([4.0, 5.0, 6.0], dtype=np.float32),
            bpm=130.0,
        )

        db.add_song(song1, features1)
        db.add_song(song2, features2)

        yield db


@pytest.fixture
def client(test_config):
    """Create a test client with mocked dependencies."""
    from vibe_dj.api.dependencies import get_config

    def override_get_config():
        return test_config

    app.dependency_overrides[get_config] = override_get_config

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_job_manager():
    """Create a mock job manager."""
    return JobManager()
