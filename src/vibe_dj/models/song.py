from dataclasses import dataclass
from typing import Optional


@dataclass
class Song:
    id: int
    file_path: str
    title: str
    artist: str
    album: str
    genre: str
    last_modified: float
    duration: Optional[int]

    def __str__(self) -> str:
        return f"{self.artist} - {self.title}"

    def __repr__(self) -> str:
        return f"Song(id={self.id}, title='{self.title}', artist='{self.artist}', album='{self.album}')"
