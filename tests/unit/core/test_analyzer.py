from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from vibe_dj.core.analyzer import AudioAnalyzer
from vibe_dj.models import Config, Features


class TestAudioAnalyzer:
    """Test suite for AudioAnalyzer."""

    @pytest.fixture()
    def analyzer(self):
        """Set up test fixtures before each test method."""
        config = Config()
        return AudioAnalyzer(config)

    @patch("vibe_dj.core.analyzer.librosa")
    def test_extract_features_success(self, mock_librosa, analyzer):
        """Test successful feature extraction from audio file."""
        mock_y = np.random.random(22050 * 10)
        mock_librosa.load.return_value = (mock_y, 22050)
        mock_librosa.feature.mfcc.return_value = np.random.random((13, 100))
        mock_librosa.feature.chroma_cqt.return_value = np.random.random((12, 100))
        mock_librosa.beat.beat_track.return_value = (120.0, None)
        mock_librosa.feature.rms.return_value = np.array([[0.5] * 100])
        mock_librosa.feature.spectral_centroid.return_value = np.array([[1000.0] * 100])
        mock_librosa.onset.onset_strength.return_value = np.array([0.8] * 100)

        features = analyzer.extract_features("/test/song.mp3")

        assert features is not None
        assert isinstance(features, Features)
        assert features.bpm == 120.0
        assert isinstance(features.feature_vector, np.ndarray)

    @patch("vibe_dj.core.analyzer.librosa")
    def test_extract_features_failure(self, mock_librosa, analyzer):
        """Test feature extraction failure handling."""
        mock_librosa.load.side_effect = Exception("Load failed")

        features = analyzer.extract_features("/test/song.mp3")

        assert features is None

    @patch("vibe_dj.core.analyzer.MutagenFile")
    def test_extract_metadata_with_tags(self, mock_mutagen, analyzer):
        """Test metadata extraction with complete tags."""
        mock_audio = MagicMock()

        def mock_get(key, default=None):
            return {
                "title": ["Test Song"],
                "artist": ["Test Artist"],
                "album": ["Test Album"],
                "genre": ["Rock"],
            }.get(key, default)

        mock_audio.get = mock_get
        mock_mutagen.return_value = mock_audio

        title, artist, album, genre = analyzer.extract_metadata("/test/song.mp3")

        assert title == "Test Song"
        assert artist == "Test Artist"
        assert album == "Test Album"
        assert genre == "Rock"

    @patch("vibe_dj.core.analyzer.MutagenFile")
    def test_extract_metadata_missing_tags(self, mock_mutagen, analyzer):
        """Test metadata extraction with missing tags."""
        mock_audio = MagicMock()
        mock_audio.get.return_value = None
        mock_mutagen.return_value = mock_audio

        title, artist, album, genre = analyzer.extract_metadata("/test/song.mp3")

        assert title == "song.mp3"
        assert artist == "Unknown"
        assert album == "Unknown"
        assert genre == "Unknown"

    @patch("vibe_dj.core.analyzer.MutagenFile")
    def test_get_duration_success(self, mock_mutagen, analyzer):
        """Test successful duration extraction."""
        mock_audio = MagicMock()
        mock_audio.info.length = 180.5
        mock_mutagen.return_value = mock_audio

        duration = analyzer.get_duration("/test/song.mp3")

        assert duration == 181

    @patch("vibe_dj.core.analyzer.MutagenFile")
    def test_get_duration_failure(self, mock_mutagen, analyzer):
        """Test duration extraction failure handling."""
        mock_mutagen.side_effect = Exception("Failed")

        duration = analyzer.get_duration("/test/song.mp3")

        assert duration is None

    @patch.object(AudioAnalyzer, "extract_metadata")
    @patch.object(AudioAnalyzer, "get_duration")
    @patch.object(AudioAnalyzer, "extract_features")
    def test_analyze_file_success(
        self, mock_extract_features, mock_get_duration, mock_extract_metadata, analyzer
    ):
        """Test complete file analysis with all components."""
        mock_extract_metadata.return_value = (
            "Test Song",
            "Test Artist",
            "Test Album",
            "Rock",
        )
        mock_get_duration.return_value = 180
        mock_extract_features.return_value = Features(
            song_id=0,
            feature_vector=np.array([1.0, 2.0, 3.0], dtype=np.float32),
            bpm=120.0,
        )

        result = analyzer.analyze_file("/test/song.mp3", 1234567890.0)

        assert result is not None
        song, features = result
        assert song.title == "Test Song"
        assert song.artist == "Test Artist"
        assert song.album == "Test Album"
        assert features.bpm == 120.0

    @patch.object(AudioAnalyzer, "extract_features")
    def test_analyze_file_no_features(self, mock_extract_features, analyzer):
        """Test file analysis when feature extraction fails."""
        mock_extract_features.return_value = None

        result = analyzer.analyze_file("/test/song.mp3", 1234567890.0)

        assert result is None
