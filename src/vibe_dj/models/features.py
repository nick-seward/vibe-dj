from typing import TYPE_CHECKING

import numpy as np
from sqlalchemy import Float, ForeignKey, Integer, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .song import Song


class Features(Base):
    """Audio feature representation for a song.

    Contains the feature vector extracted from audio analysis and
    the detected BPM (beats per minute).
    """

    __tablename__ = "features"

    song_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("songs.id", ondelete="CASCADE"), primary_key=True
    )
    _feature_vector_bytes: Mapped[bytes] = mapped_column(
        "feature_vector", LargeBinary, nullable=False
    )
    bpm: Mapped[float] = mapped_column(Float)

    song: Mapped["Song"] = relationship("Song", back_populates="features")

    @property
    def feature_vector(self) -> np.ndarray:
        """Get the feature vector as a numpy array.

        :return: Feature vector as np.ndarray with dtype float32
        """
        return np.frombuffer(self._feature_vector_bytes, dtype=np.float32)

    @feature_vector.setter
    def feature_vector(self, value: np.ndarray) -> None:
        """Set the feature vector from a numpy array.

        :param value: Feature vector as np.ndarray
        """
        self._feature_vector_bytes = value.astype(np.float32).tobytes()

    def to_bytes(self) -> bytes:
        """Convert feature vector to bytes for database storage.

        :return: Byte representation of the feature vector
        """
        return self._feature_vector_bytes

    @classmethod
    def from_bytes(cls, song_id: int, vector_bytes: bytes, bpm: float) -> "Features":
        """Reconstruct Features from bytes stored in database.

        :param song_id: ID of the song these features belong to
        :param vector_bytes: Byte representation of the feature vector
        :param bpm: Beats per minute value
        :return: Features instance reconstructed from bytes
        """
        instance = cls()
        instance.song_id = song_id
        instance._feature_vector_bytes = vector_bytes
        instance.bpm = bpm
        return instance

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
