import tempfile
import unittest
from pathlib import Path

import numpy as np

from vibe_dj.core.similarity import SimilarityIndex
from vibe_dj.models import Config


class TestSimilarityIndex(unittest.TestCase):
    """Test suite for SimilarityIndex class."""

    def setUp(self):
        """Set up test fixtures with temporary index file before each test method."""
        self.temp_index = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
        self.temp_index.close()

        self.config = Config(faiss_index_path=self.temp_index.name)
        self.index = SimilarityIndex(self.config)

        self.test_vectors = np.array(
            [
                [1.0, 2.0, 3.0, 4.0],
                [2.0, 3.0, 4.0, 5.0],
                [3.0, 4.0, 5.0, 6.0],
                [10.0, 11.0, 12.0, 13.0],
            ],
            dtype=np.float32,
        )

        self.test_song_ids = np.array([1, 2, 3, 4], dtype=np.int64)

    def tearDown(self):
        Path(self.temp_index.name).unlink(missing_ok=True)

    def test_build_index(self):
        self.index.build_index(self.test_vectors, self.test_song_ids)

        self.assertEqual(self.index.dimension, 4)
        self.assertEqual(self.index.size, 4)

    def test_build_index_empty_vectors(self):
        empty_vectors = np.array([], dtype=np.float32).reshape(0, 4)
        empty_ids = np.array([], dtype=np.int64)

        with self.assertRaises(ValueError):
            self.index.build_index(empty_vectors, empty_ids)

    def test_build_index_mismatched_lengths(self):
        vectors = np.array([[1.0, 2.0, 3.0, 4.0]], dtype=np.float32)
        ids = np.array([1, 2], dtype=np.int64)

        with self.assertRaises(ValueError):
            self.index.build_index(vectors, ids)

    def test_search(self):
        self.index.build_index(self.test_vectors, self.test_song_ids)

        query = np.array([1.1, 2.1, 3.1, 4.1], dtype=np.float32)
        distances, indices = self.index.search(query, k=2)

        self.assertEqual(len(distances), 2)
        self.assertEqual(len(indices), 2)
        self.assertEqual(indices[0], 1)

    def test_search_without_index(self):
        query = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)

        with self.assertRaises(RuntimeError):
            self.index.search(query)

    def test_search_wrong_dimension(self):
        self.index.build_index(self.test_vectors, self.test_song_ids)

        query = np.array([1.0, 2.0], dtype=np.float32)

        with self.assertRaises(ValueError):
            self.index.search(query)

    def test_save_and_load(self):
        self.index.build_index(self.test_vectors, self.test_song_ids)
        self.index.save()

        new_index = SimilarityIndex(self.config)
        new_index.load()

        self.assertEqual(new_index.dimension, 4)
        self.assertEqual(new_index.size, 4)

        query = np.array([1.1, 2.1, 3.1, 4.1], dtype=np.float32)
        distances, indices = new_index.search(query, k=2)

        self.assertEqual(indices[0], 1)

    def test_save_without_index(self):
        with self.assertRaises(RuntimeError):
            self.index.save()

    def test_add_vectors(self):
        self.index.build_index(self.test_vectors, self.test_song_ids)

        new_vectors = np.array([[20.0, 21.0, 22.0, 23.0]], dtype=np.float32)
        new_ids = np.array([5], dtype=np.int64)

        self.index.add_vectors(new_vectors, new_ids)

        self.assertEqual(self.index.size, 5)

    def test_add_vectors_wrong_dimension(self):
        self.index.build_index(self.test_vectors, self.test_song_ids)

        new_vectors = np.array([[20.0, 21.0]], dtype=np.float32)
        new_ids = np.array([5], dtype=np.int64)

        with self.assertRaises(ValueError):
            self.index.add_vectors(new_vectors, new_ids)

    def test_remove_vectors(self):
        self.index.build_index(self.test_vectors, self.test_song_ids)

        self.index.remove_vectors([1, 2])

        self.assertEqual(self.index.size, 2)


if __name__ == "__main__":
    unittest.main()
