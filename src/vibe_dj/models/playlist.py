from dataclasses import dataclass, field
from datetime import datetime
from typing import List
from .song import Song


@dataclass
class Playlist:
    songs: List[Song] = field(default_factory=list)
    seed_songs: List[Song] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def __len__(self) -> int:
        return len(self.songs)

    def add_song(self, song: Song) -> None:
        self.songs.append(song)

    def remove_song(self, song_id: int) -> bool:
        for i, song in enumerate(self.songs):
            if song.id == song_id:
                self.songs.pop(i)
                return True
        return False

    def get_song_ids(self) -> List[int]:
        return [song.id for song in self.songs]

    def __repr__(self) -> str:
        return f"Playlist(songs={len(self.songs)}, seeds={len(self.seed_songs)})"
