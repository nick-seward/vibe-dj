from typing import Any, Dict, Optional

from loguru import logger

from vibe_dj.models import Config, Playlist
from vibe_dj.services.navidrome_client import NavidromeClient
from vibe_dj.services.url_security import UnsafeOutboundURLError, validate_outbound_url


class NavidromeSyncService:
    """
    Service for syncing playlists to Navidrome server.

    Handles credential resolution, song matching, and playlist
    creation/update operations.
    """

    def __init__(self, config: Config):
        """Initialize Navidrome sync service.

        :param config: Configuration object
        """
        self.config = config

    def sync_playlist(
        self,
        playlist: Playlist,
        playlist_name: Optional[str] = None,
        navidrome_url: Optional[str] = None,
        navidrome_username: Optional[str] = None,
        navidrome_password: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sync a generated playlist to Navidrome server.

        Credentials are resolved in the following order:
        1. Explicit parameters
        2. Config file values

        :param playlist: Generated Playlist object
        :param playlist_name: Name for the playlist (optional, defaults to 'Vibe DJ Playlist')
        :param navidrome_url: Navidrome server URL (optional)
        :param navidrome_username: Navidrome username (optional)
        :param navidrome_password: Navidrome password (optional)
        :return: Dictionary with sync results containing keys: 'success', 'playlist_id',
                 'playlist_name', 'matched_count', 'total_count', 'skipped_songs',
                 'error', and 'action'
        """
        url = navidrome_url or self.config.navidrome_url
        username = navidrome_username or self.config.navidrome_username
        password = navidrome_password or self.config.navidrome_password
        playlist_name = playlist_name or "Vibe DJ Playlist"

        if not all([url, username, password]):
            logger.warning("Navidrome sync requested but credentials not provided")
            logger.warning("Provide via parameters or config file")
            return {
                "success": False,
                "playlist_id": None,
                "playlist_name": playlist_name,
                "matched_count": 0,
                "total_count": len(playlist.songs),
                "skipped_songs": [],
                "error": "Missing credentials",
                "action": None,
            }

        try:
            safe_url = validate_outbound_url(url)
        except UnsafeOutboundURLError as e:
            logger.warning(f"Navidrome sync blocked due to unsafe URL: {e}")
            return {
                "success": False,
                "playlist_id": None,
                "playlist_name": playlist_name,
                "matched_count": 0,
                "total_count": len(playlist.songs),
                "skipped_songs": [],
                "error": str(e),
                "action": None,
            }

        try:
            logger.info(f"Syncing playlist to Navidrome at {safe_url}...")

            client = NavidromeClient(safe_url, username, password)

            song_ids = []
            matched_count = 0
            skipped_songs = []

            for song in playlist.songs:
                song_id = client.search_song(
                    title=song.title, artist=song.artist, album=song.album
                )

                if song_id:
                    song_ids.append(song_id)
                    matched_count += 1
                else:
                    skipped_songs.append(f"{song.title} by {song.artist}")

            if not song_ids:
                logger.error("No songs could be matched on Navidrome. Sync aborted.")
                return {
                    "success": False,
                    "playlist_id": None,
                    "playlist_name": playlist_name,
                    "matched_count": 0,
                    "total_count": len(playlist.songs),
                    "skipped_songs": skipped_songs,
                    "error": "No songs matched",
                    "action": None,
                }

            if skipped_songs:
                logger.warning(
                    f"{len(skipped_songs)} song(s) could not be matched on Navidrome"
                )
                for skipped in skipped_songs[:5]:
                    logger.debug(f"Skipped: {skipped}")
                if len(skipped_songs) > 5:
                    logger.debug(f"... and {len(skipped_songs) - 5} more")

            existing_playlist = client.get_playlist_by_name(playlist_name)

            if existing_playlist:
                playlist_id = existing_playlist["id"]
                logger.info(
                    f"Updating existing playlist '{playlist_name}' (ID: {playlist_id})..."
                )

                if client.replace_playlist_songs(playlist_id, song_ids):
                    logger.info(
                        f"Playlist '{playlist_name}' successfully updated on Navidrome"
                    )
                    logger.info(f"Matched: {matched_count}/{len(playlist.songs)} songs")
                    return {
                        "success": True,
                        "playlist_id": playlist_id,
                        "playlist_name": playlist_name,
                        "matched_count": matched_count,
                        "total_count": len(playlist.songs),
                        "skipped_songs": skipped_songs,
                        "error": None,
                        "action": "updated",
                    }
                else:
                    logger.error(f"Failed to update playlist '{playlist_name}'")
                    return {
                        "success": False,
                        "playlist_id": playlist_id,
                        "playlist_name": playlist_name,
                        "matched_count": matched_count,
                        "total_count": len(playlist.songs),
                        "skipped_songs": skipped_songs,
                        "error": "Update failed",
                        "action": None,
                    }
            else:
                logger.info(f"Creating new playlist '{playlist_name}'...")

                playlist_id = client.create_playlist(playlist_name, song_ids)

                if playlist_id:
                    logger.info(
                        f"Playlist '{playlist_name}' successfully created on Navidrome (ID: {playlist_id})"
                    )
                    logger.info(f"Matched: {matched_count}/{len(playlist.songs)} songs")
                    return {
                        "success": True,
                        "playlist_id": playlist_id,
                        "playlist_name": playlist_name,
                        "matched_count": matched_count,
                        "total_count": len(playlist.songs),
                        "skipped_songs": skipped_songs,
                        "error": None,
                        "action": "created",
                    }
                else:
                    logger.error(f"Failed to create playlist '{playlist_name}'")
                    return {
                        "success": False,
                        "playlist_id": None,
                        "playlist_name": playlist_name,
                        "matched_count": matched_count,
                        "total_count": len(playlist.songs),
                        "skipped_songs": skipped_songs,
                        "error": "Creation failed",
                        "action": None,
                    }

        except Exception as e:
            logger.exception(f"Error syncing to Navidrome: {e}")
            return {
                "success": False,
                "playlist_id": None,
                "playlist_name": playlist_name,
                "matched_count": 0,
                "total_count": len(playlist.songs),
                "skipped_songs": [],
                "error": str(e),
                "action": None,
            }
