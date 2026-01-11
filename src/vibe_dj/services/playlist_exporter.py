import json
from typing import Optional

from loguru import logger

from ..models import Config, Playlist


class PlaylistExporter:
    """Exports playlists to various file formats.

    Supports M3U, M3U8, and JSON export formats.
    """

    def __init__(self, config: Config):
        """Initialize the playlist exporter with configuration.

        :param config: Configuration object containing default output paths
        """
        self.config = config

    def _write_m3u(
        self, playlist: Playlist, output_path: str, format_name: str
    ) -> None:
        """Write playlist to M3U/M3U8 format.

        :param playlist: Playlist object to export
        :param output_path: Output file path
        :param format_name: Format name for logging ('M3U' or 'M3U8')
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for song in playlist.songs:
                duration = song.duration or -1
                f.write(f"#EXTINF:{duration},{song.artist} - {song.title}\n")
                f.write(f"{song.file_path}\n")

        logger.info(f"Exported {format_name} playlist to {output_path}")

    def export_m3u(self, playlist: Playlist, output_path: Optional[str] = None) -> None:
        """Export playlist to M3U format.

        :param playlist: Playlist object to export
        :param output_path: Output file path (defaults to config.playlist_output)
        """
        if output_path is None:
            output_path = self.config.playlist_output
        self._write_m3u(playlist, output_path, "M3U")

    def export_m3u8(self, playlist: Playlist, output_path: str) -> None:
        """Export playlist to M3U8 format (UTF-8 encoded M3U).

        :param playlist: Playlist object to export
        :param output_path: Output file path
        """
        self._write_m3u(playlist, output_path, "M3U8")

    def export_json(self, playlist: Playlist, output_path: str) -> None:
        """Export playlist to JSON format with full metadata.

        Includes creation timestamp, seed songs, and detailed song information.

        :param playlist: Playlist object to export
        :param output_path: Output file path
        """
        data = {
            "created_at": playlist.created_at.isoformat(),
            "seed_songs": [
                {
                    "id": song.id,
                    "title": song.title,
                    "artist": song.artist,
                    "file_path": song.file_path,
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
                    "file_path": song.file_path,
                }
                for song in playlist.songs
            ],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported JSON playlist to {output_path}")

    def export(
        self, playlist: Playlist, output_path: str, output_format: str = "m3u"
    ) -> None:
        """Export playlist to specified format.

        :param playlist: Playlist object to export
        :param output_path: Output file path
        :param output_format: Export format ('m3u', 'm3u8', or 'json')
        :raises ValueError: If format is not supported
        """
        output_format = output_format.lower()

        if output_format == "m3u":
            self.export_m3u(playlist, output_path)
        elif output_format == "m3u8":
            self.export_m3u8(playlist, output_path)
        elif output_format == "json":
            self.export_json(playlist, output_path)
        else:
            raise ValueError(
                f"Unsupported format: {output_format}. Use 'm3u', 'm3u8', or 'json'"
            )
