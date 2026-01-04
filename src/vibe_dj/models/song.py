from dataclasses import dataclass
from typing import Optional


@dataclass
class Song:
    """Represents a song with metadata.

    Contains all metadata extracted from audio files including
    title, artist, album, genre, file information, and duration.
    """

    id: int
    file_path: str
    title: str
    artist: str
    album: str
    genre: str
    last_modified: float
    duration: Optional[int]

    def __str__(self) -> str:
        """Return human-readable string representation.

        :return: String in format 'Artist - Title'
        """
        return f"{self.artist} - {self.title}"

    def __repr__(self) -> str:
        """Return detailed string representation for debugging.

        :return: String showing id, title, artist, and album
        """
        return f"Song(id={self.id}, title='{self.title}', artist='{self.artist}', album='{self.album}')"
