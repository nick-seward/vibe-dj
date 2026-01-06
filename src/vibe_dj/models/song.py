from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .features import Features


class Song(Base):
    """Represents a song with metadata.

    Contains all metadata extracted from audio files including
    title, artist, album, genre, file information, and duration.
    """

    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[str] = mapped_column(String)
    artist: Mapped[str] = mapped_column(String)
    album: Mapped[str] = mapped_column(String)
    genre: Mapped[str] = mapped_column(String)
    last_modified: Mapped[float] = mapped_column(Float)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    features: Mapped[Optional["Features"]] = relationship(
        "Features", back_populates="song", uselist=False, cascade="all, delete-orphan"
    )

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
