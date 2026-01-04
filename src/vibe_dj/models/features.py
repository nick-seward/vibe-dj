from dataclasses import dataclass

import numpy as np


@dataclass
class Features:
    song_id: int
    feature_vector: np.ndarray
    bpm: float

    def to_bytes(self) -> bytes:
        return self.feature_vector.tobytes()

    @classmethod
    def from_bytes(cls, song_id: int, vector_bytes: bytes, bpm: float) -> "Features":
        feature_vector = np.frombuffer(vector_bytes, dtype=np.float32)
        return cls(song_id=song_id, feature_vector=feature_vector, bpm=bpm)

    @property
    def dimension(self) -> int:
        return len(self.feature_vector)

    def __repr__(self) -> str:
        return f"Features(song_id={self.song_id}, bpm={self.bpm:.2f}, dim={self.dimension})"
