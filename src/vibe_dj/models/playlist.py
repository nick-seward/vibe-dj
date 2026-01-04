from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from .song import Song


@dataclass
class Playlist:
    """Represents a generated playlist of songs.

    Contains the list of songs in the playlist, the seed songs used
    for generation, and creation timestamp.
    """

    songs: List[Song] = field(default_factory=list)
    seed_songs: List[Song] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def __len__(self) -> int:
        """Get the number of songs in the playlist.

        :return: Number of songs
        """
        return len(self.songs)

    def add_song(self, song: Song) -> None:
        """Add a song to the playlist.

        :param song: Song object to add
        """
        self.songs.append(song)

    def remove_song(self, song_id: int) -> bool:
        """Remove a song from the playlist by its ID.

        :param song_id: ID of the song to remove
        :return: True if song was found and removed, False otherwise
        """
        for i, song in enumerate(self.songs):
            if song.id == song_id:
                self.songs.pop(i)
                return True
        return False

    def get_song_ids(self) -> List[int]:
        """Get list of all song IDs in the playlist.

        :return: List of song IDs
        """
        return [song.id for song in self.songs]

    def __repr__(self) -> str:
        """Return string representation of Playlist.

        :return: String showing song count and seed count
        """
        return f"Playlist(songs={len(self.songs)}, seeds={len(self.seed_songs)})"
