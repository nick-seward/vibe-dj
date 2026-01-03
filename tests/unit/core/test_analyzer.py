import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from vibe_dj.core.analyzer import AudioAnalyzer
from vibe_dj.models import Config, Features


class TestAudioAnalyzer(unittest.TestCase):
    def setUp(self):
        self.config = Config()
        self.analyzer = AudioAnalyzer(self.config)

    @patch('vibe_dj.core.analyzer.librosa')
    def test_extract_features_success(self, mock_librosa):
        mock_y = np.random.random(22050 * 10)
        mock_librosa.load.return_value = (mock_y, 22050)
        mock_librosa.feature.mfcc.return_value = np.random.random((13, 100))
        mock_librosa.feature.chroma_cqt.return_value = np.random.random((12, 100))
        mock_librosa.beat.beat_track.return_value = (120.0, None)
        mock_librosa.feature.rms.return_value = np.array([[0.5] * 100])
        mock_librosa.feature.spectral_centroid.return_value = np.array([[1000.0] * 100])
        mock_librosa.onset.onset_strength.return_value = np.array([0.8] * 100)
        
        features = self.analyzer.extract_features("/test/song.mp3")
        
        self.assertIsNotNone(features)
        self.assertIsInstance(features, Features)
        self.assertEqual(features.bpm, 120.0)
        self.assertIsInstance(features.feature_vector, np.ndarray)

    @patch('vibe_dj.core.analyzer.librosa')
    def test_extract_features_failure(self, mock_librosa):
        mock_librosa.load.side_effect = Exception("Load failed")
        
        features = self.analyzer.extract_features("/test/song.mp3")
        
        self.assertIsNone(features)

    @patch('vibe_dj.core.analyzer.MutagenFile')
    def test_extract_metadata_with_tags(self, mock_mutagen):
        mock_audio = MagicMock()
        
        def mock_get(key, default=None):
            return {
                "title": ["Test Song"],
                "artist": ["Test Artist"],
                "album": ["Test Album"],
                "genre": ["Rock"]
            }.get(key, default)
        
        mock_audio.get = mock_get
        mock_mutagen.return_value = mock_audio
        
        title, artist, album, genre = self.analyzer.extract_metadata("/test/song.mp3")
        
        self.assertEqual(title, "Test Song")
        self.assertEqual(artist, "Test Artist")
        self.assertEqual(album, "Test Album")
        self.assertEqual(genre, "Rock")

    @patch('vibe_dj.core.analyzer.MutagenFile')
    def test_extract_metadata_missing_tags(self, mock_mutagen):
        mock_audio = MagicMock()
        mock_audio.get.return_value = None
        mock_mutagen.return_value = mock_audio
        
        title, artist, album, genre = self.analyzer.extract_metadata("/test/song.mp3")
        
        self.assertEqual(title, "song.mp3")
        self.assertEqual(artist, "Unknown")
        self.assertEqual(album, "Unknown")
        self.assertEqual(genre, "Unknown")

    @patch('vibe_dj.core.analyzer.MutagenFile')
    def test_get_duration_success(self, mock_mutagen):
        mock_audio = MagicMock()
        mock_audio.info.length = 180.5
        mock_mutagen.return_value = mock_audio
        
        duration = self.analyzer.get_duration("/test/song.mp3")
        
        self.assertEqual(duration, 181)

    @patch('vibe_dj.core.analyzer.MutagenFile')
    def test_get_duration_failure(self, mock_mutagen):
        mock_mutagen.side_effect = Exception("Failed")
        
        duration = self.analyzer.get_duration("/test/song.mp3")
        
        self.assertIsNone(duration)

    @patch.object(AudioAnalyzer, 'extract_metadata')
    @patch.object(AudioAnalyzer, 'get_duration')
    @patch.object(AudioAnalyzer, 'extract_features')
    def test_analyze_file_success(self, mock_extract_features, mock_get_duration, mock_extract_metadata):
        mock_extract_metadata.return_value = ("Test Song", "Test Artist", "Test Album", "Rock")
        mock_get_duration.return_value = 180
        mock_extract_features.return_value = Features(
            song_id=0,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0
        )
        
        result = self.analyzer.analyze_file("/test/song.mp3", 1234567890.0)
        
        self.assertIsNotNone(result)
        song, features = result
        self.assertEqual(song.title, "Test Song")
        self.assertEqual(song.artist, "Test Artist")
        self.assertEqual(song.album, "Test Album")
        self.assertEqual(features.bpm, 120.0)

    @patch.object(AudioAnalyzer, 'extract_features')
    def test_analyze_file_no_features(self, mock_extract_features):
        mock_extract_features.return_value = None
        
        result = self.analyzer.analyze_file("/test/song.mp3", 1234567890.0)
        
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
