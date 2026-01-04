import unittest

import numpy as np

from vibe_dj.models.features import Features


class TestFeatures(unittest.TestCase):
    def test_features_creation(self):
        vector = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        features = Features(song_id=1, feature_vector=vector, bpm=120.5)

        self.assertEqual(features.song_id, 1)
        self.assertEqual(features.bpm, 120.5)
        self.assertEqual(features.dimension, 4)
        np.testing.assert_array_equal(features.feature_vector, vector)

    def test_to_bytes(self):
        vector = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        features = Features(song_id=1, feature_vector=vector, bpm=120.0)

        bytes_data = features.to_bytes()
        self.assertIsInstance(bytes_data, bytes)
        self.assertEqual(len(bytes_data), 12)  # 3 floats * 4 bytes

    def test_from_bytes(self):
        original_vector = np.array([1.5, 2.5, 3.5, 4.5], dtype=np.float32)
        bytes_data = original_vector.tobytes()

        features = Features.from_bytes(song_id=42, vector_bytes=bytes_data, bpm=130.0)

        self.assertEqual(features.song_id, 42)
        self.assertEqual(features.bpm, 130.0)
        np.testing.assert_array_almost_equal(features.feature_vector, original_vector)

    def test_dimension_property(self):
        vector = np.array([1.0] * 50, dtype=np.float32)
        features = Features(song_id=1, feature_vector=vector, bpm=120.0)

        self.assertEqual(features.dimension, 50)


if __name__ == "__main__":
    unittest.main()
