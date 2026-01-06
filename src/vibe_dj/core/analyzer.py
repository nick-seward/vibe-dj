import math
from typing import Optional, Tuple

import librosa
import numpy as np
from loguru import logger
from mutagen import File as MutagenFile

from ..models import Config, Features, Song


class AudioAnalyzer:
    """Analyzes audio files to extract features and metadata.

    This class handles the extraction of audio features using librosa,
    metadata extraction using mutagen, and duration calculation for
    music files.
    """

    def __init__(self, config: Config):
        """Initialize the AudioAnalyzer with configuration.

        :param config: Configuration object containing analysis parameters
        """
        self.config = config

    def extract_features(self, file_path: str) -> Optional[Features]:
        """Extract audio features from a music file.

        Extracts MFCC, chroma, tempo, loudness, spectral centroid, and
        derived features like danceability and acousticness using librosa.

        :param file_path: Path to the audio file to analyze
        :return: Features object containing the feature vector and BPM,
                 or None if extraction fails
        """
        try:
            y, sr = librosa.load(
                file_path,
                sr=self.config.sample_rate,
                mono=True,
                duration=self.config.max_duration,
            )

            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=self.config.n_mfcc).mean(
                axis=1
            )
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
            chroma = np.pad(chroma, (0, 32 - len(chroma)), mode="constant")

            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            tempo = float(tempo) if np.isscalar(tempo) else float(tempo[0])

            loudness = float(librosa.feature.rms(y=y).mean())
            centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
            onset_strength = float(librosa.onset.onset_strength(y=y, sr=sr).mean())
            danceability = float(onset_strength / 10.0)
            acousticness = float(1.0 - (loudness + centroid / sr))

            del y

            feature_vector = np.concatenate(
                [mfcc, chroma, [tempo, loudness, centroid, danceability, acousticness]]
            ).astype(np.float32)

            features = Features()
            features.feature_vector = feature_vector
            features.bpm = float(tempo)
            return features
        except Exception as e:
            logger.error(f"Failed to extract features from {file_path}: {e}")
            return None

    def extract_metadata(self, file_path: str) -> Tuple[str, str, str, str]:
        """Extract metadata tags from an audio file.

        Extracts title, artist, album, and genre from the audio file's
        metadata tags. Falls back to filename and default values if
        metadata is missing or extraction fails.

        :param file_path: Path to the audio file
        :return: Tuple of (title, artist, album, genre)
        """
        try:
            audio = MutagenFile(file_path, easy=True)
            title = (audio.get("title", [None]) or [None])[0]
            if not title:
                import os

                title = os.path.basename(file_path)

            artist = (audio.get("artist", ["Unknown"]) or ["Unknown"])[0]
            album = (audio.get("album", ["Unknown"]) or ["Unknown"])[0]
            genre = (audio.get("genre", ["Unknown"]) or ["Unknown"])[0]

            return title, artist, album, genre
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {e}")
            import os

            return os.path.basename(file_path), "Unknown", "Unknown", "Unknown"

    def get_duration(self, file_path: str) -> Optional[int]:
        """Get the duration of an audio file in seconds.

        :param file_path: Path to the audio file
        :return: Duration in seconds (rounded up), or None if extraction fails
        """
        try:
            audio = MutagenFile(file_path)
            if audio and audio.info:
                return int(math.ceil(audio.info.length))
        except Exception as e:
            logger.error(f"Failed to get duration from {file_path}: {e}")
        return None

    def analyze_file(
        self, file_path: str, last_modified: float
    ) -> Optional[Tuple[Song, Features]]:
        """Perform complete analysis of an audio file.

        Extracts both metadata and audio features from the file,
        combining them into Song and Features objects.

        :param file_path: Path to the audio file to analyze
        :param last_modified: Last modification timestamp of the file
        :return: Tuple of (Song, Features) if successful, None if feature
                 extraction fails
        """
        title, artist, album, genre = self.extract_metadata(file_path)
        duration = self.get_duration(file_path)
        features = self.extract_features(file_path)

        if features is None:
            return None

        song = Song(
            id=0,
            file_path=file_path,
            title=title,
            artist=artist,
            album=album,
            genre=genre,
            last_modified=last_modified,
            duration=duration,
        )

        return (song, features)
