from dataclasses import dataclass

import numpy as np


@dataclass
class Features:
    """Audio feature representation for a song.

    Contains the feature vector extracted from audio analysis and
    the detected BPM (beats per minute).
    """

    song_id: int
    feature_vector: np.ndarray
    bpm: float

    def to_bytes(self) -> bytes:
        """Convert feature vector to bytes for database storage.

        :return: Byte representation of the feature vector
        """
        return self.feature_vector.tobytes()

    @classmethod
    def from_bytes(cls, song_id: int, vector_bytes: bytes, bpm: float) -> "Features":
        """Reconstruct Features from bytes stored in database.

        :param song_id: ID of the song these features belong to
        :param vector_bytes: Byte representation of the feature vector
        :param bpm: Beats per minute value
        :return: Features instance reconstructed from bytes
        """
        feature_vector = np.frombuffer(vector_bytes, dtype=np.float32)
        return cls(song_id=song_id, feature_vector=feature_vector, bpm=bpm)

    @property
    def dimension(self) -> int:
        """Get the dimensionality of the feature vector.

        :return: Number of dimensions in the feature vector
        """
        return len(self.feature_vector)

    def __repr__(self) -> str:
        """Return string representation of Features.

        :return: String showing song_id, bpm, and dimension
        """
        return f"Features(song_id={self.song_id}, bpm={self.bpm:.2f}, dim={self.dimension})"
