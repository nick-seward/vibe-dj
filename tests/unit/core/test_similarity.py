import tempfile
from pathlib import Path

import numpy as np
import pytest

from vibe_dj.core.similarity import SimilarityIndex
from vibe_dj.models import Config


class TestSimilarityIndex:
    """Test suite for SimilarityIndex."""

    @pytest.fixture()
    def similarity_env(self):
        """Set up test fixtures with temporary index file before each test method."""
        temp_index = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
        temp_index.close()

        config = Config(faiss_index_path=temp_index.name)
        index = SimilarityIndex(config)

        test_vectors = np.array(
            [
                [1.0, 2.0, 3.0, 4.0],
                [2.0, 3.0, 4.0, 5.0],
                [3.0, 4.0, 5.0, 6.0],
                [10.0, 11.0, 12.0, 13.0],
            ],
            dtype=np.float32,
        )

        test_song_ids = np.array([1, 2, 3, 4], dtype=np.int64)

        yield config, index, test_vectors, test_song_ids

        Path(temp_index.name).unlink(missing_ok=True)

    def test_build_index(self, similarity_env):
        config, index, test_vectors, test_song_ids = similarity_env
        index.build_index(test_vectors, test_song_ids)

        assert index.dimension == 4
        assert index.size == 4

    def test_build_index_empty_vectors(self, similarity_env):
        config, index, test_vectors, test_song_ids = similarity_env
        empty_vectors = np.array([], dtype=np.float32).reshape(0, 4)
        empty_ids = np.array([], dtype=np.int64)

        with pytest.raises(ValueError):
            index.build_index(empty_vectors, empty_ids)

    def test_build_index_mismatched_lengths(self, similarity_env):
        config, index, test_vectors, test_song_ids = similarity_env
        vectors = np.array([[1.0, 2.0, 3.0, 4.0]], dtype=np.float32)
        ids = np.array([1, 2], dtype=np.int64)

        with pytest.raises(ValueError):
            index.build_index(vectors, ids)

    def test_search(self, similarity_env):
        config, index, test_vectors, test_song_ids = similarity_env
        index.build_index(test_vectors, test_song_ids)

        query = np.array([1.1, 2.1, 3.1, 4.1], dtype=np.float32)
        distances, indices = index.search(query, k=2)

        assert len(distances) == 2
        assert len(indices) == 2
        assert indices[0] == 1

    def test_search_without_index(self, similarity_env):
        config, index, test_vectors, test_song_ids = similarity_env
        query = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)

        with pytest.raises(RuntimeError):
            index.search(query)

    def test_search_wrong_dimension(self, similarity_env):
        config, index, test_vectors, test_song_ids = similarity_env
        index.build_index(test_vectors, test_song_ids)

        query = np.array([1.0, 2.0], dtype=np.float32)

        with pytest.raises(ValueError):
            index.search(query)

    def test_save_and_load(self, similarity_env):
        config, index, test_vectors, test_song_ids = similarity_env
        index.build_index(test_vectors, test_song_ids)
        index.save()

        new_index = SimilarityIndex(config)
        new_index.load()

        assert new_index.dimension == 4
        assert new_index.size == 4

        query = np.array([1.1, 2.1, 3.1, 4.1], dtype=np.float32)
        distances, indices = new_index.search(query, k=2)

        assert indices[0] == 1

    def test_save_without_index(self, similarity_env):
        config, index, test_vectors, test_song_ids = similarity_env
        with pytest.raises(RuntimeError):
            index.save()

    def test_add_vectors(self, similarity_env):
        config, index, test_vectors, test_song_ids = similarity_env
        index.build_index(test_vectors, test_song_ids)

        new_vectors = np.array([[20.0, 21.0, 22.0, 23.0]], dtype=np.float32)
        new_ids = np.array([5], dtype=np.int64)

        index.add_vectors(new_vectors, new_ids)

        assert index.size == 5

    def test_add_vectors_wrong_dimension(self, similarity_env):
        config, index, test_vectors, test_song_ids = similarity_env
        index.build_index(test_vectors, test_song_ids)

        new_vectors = np.array([[20.0, 21.0]], dtype=np.float32)
        new_ids = np.array([5], dtype=np.int64)

        with pytest.raises(ValueError):
            index.add_vectors(new_vectors, new_ids)

    def test_remove_vectors(self, similarity_env):
        config, index, test_vectors, test_song_ids = similarity_env
        index.build_index(test_vectors, test_song_ids)

        index.remove_vectors([1, 2])

        assert index.size == 2
