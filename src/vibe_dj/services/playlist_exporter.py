import json
from typing import Optional
from loguru import logger
from ..models import Playlist, Config


class PlaylistExporter:
    def __init__(self, config: Config):
        self.config = config

    def export_m3u(self, playlist: Playlist, output_path: Optional[str] = None) -> None:
        if output_path is None:
            output_path = self.config.playlist_output
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for song in playlist.songs:
                duration = song.duration if song.duration else -1
                f.write(f"#EXTINF:{duration},{song.artist} - {song.title}\n")
                f.write(f"{song.file_path}\n")
        
        logger.info(f"Exported M3U playlist to {output_path}")

    def export_m3u8(self, playlist: Playlist, output_path: str) -> None:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for song in playlist.songs:
                duration = song.duration if song.duration else -1
                f.write(f"#EXTINF:{duration},{song.artist} - {song.title}\n")
                f.write(f"{song.file_path}\n")
        
        logger.info(f"Exported M3U8 playlist to {output_path}")

    def export_json(self, playlist: Playlist, output_path: str) -> None:
        data = {
            "created_at": playlist.created_at.isoformat(),
            "seed_songs": [
                {
                    "id": song.id,
                    "title": song.title,
                    "artist": song.artist,
                    "file_path": song.file_path
                }
                for song in playlist.seed_songs
            ],
            "songs": [
                {
                    "id": song.id,
                    "title": song.title,
                    "artist": song.artist,
                    "genre": song.genre,
                    "duration": song.duration,
                    "file_path": song.file_path
                }
                for song in playlist.songs
            ]
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported JSON playlist to {output_path}")

    def export(self, playlist: Playlist, output_path: str, format: str = "m3u") -> None:
        format = format.lower()
        
        if format == "m3u":
            self.export_m3u(playlist, output_path)
        elif format == "m3u8":
            self.export_m3u8(playlist, output_path)
        elif format == "json":
            self.export_json(playlist, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'm3u', 'm3u8', or 'json'")
