import click
import json
import os
from pathlib import Path
from loguru import logger
from .models import Config
from .core import MusicDatabase, AudioAnalyzer, SimilarityIndex, LibraryIndexer
from .services import PlaylistGenerator, PlaylistExporter, NavidromeClient


@click.group()
def cli():
    pass


@cli.command()
@click.argument("library_path")
@click.option("--config", type=click.Path(exists=True), help="Path to config JSON file")
def index(library_path, config):
    """Index the music library at LIBRARY_PATH."""
    if config:
        cfg = Config.from_file(config)
    else:
        cfg = Config()
    
    with MusicDatabase(cfg) as db:
        analyzer = AudioAnalyzer(cfg)
        similarity_index = SimilarityIndex(cfg)
        indexer = LibraryIndexer(cfg, db, analyzer, similarity_index)
        
        indexer.index_library(library_path)


@cli.command()
@click.option("--seeds-json", type=click.Path(exists=True), required=True,
              help='JSON file with seeds: {"seeds": [{"title": "...", "artist": "...", "album": "..."}]}')
@click.option("--output", type=click.Path(), default=None,
              help="Output playlist file path")
@click.option("--format", type=click.Choice(['m3u', 'm3u8', 'json'], case_sensitive=False),
              default='m3u', help="Output format (default: m3u)")
@click.option("--length", type=int, default=20, help="Number of songs in playlist (default: 20)")
@click.option("--bpm-jitter", type=float, default=5.0, 
              help="BPM jitter percentage for sorting (default: 5.0)")
@click.option("--config", type=click.Path(exists=True), help="Path to config JSON file")
@click.option("--sync-to-navidrome", is_flag=True, default=False,
              help="Sync playlist to Navidrome server")
@click.option("--navidrome-url", type=str, default=None,
              help="Navidrome server URL (e.g., http://192.168.1.100:4533)")
@click.option("--navidrome-username", type=str, default=None,
              help="Navidrome username")
@click.option("--navidrome-password", type=str, default=None,
              help="Navidrome password")
@click.option("--playlist-name", type=str, default=None,
              help="Name for the playlist on Navidrome (defaults to output filename)")
def playlist(seeds_json, output, format, length, bpm_jitter, config, 
             sync_to_navidrome, navidrome_url, navidrome_username, 
             navidrome_password, playlist_name):
    """Generate a playlist from seed songs (requires title, artist, and album for each seed)."""
    if config:
        cfg = Config.from_file(config)
    else:
        cfg = Config()
    
    if output is None:
        output = cfg.playlist_output
    
    with open(seeds_json) as f:
        data = json.load(f)
        seeds = data.get("seeds", [])

    if not seeds:
        click.echo("Error: Provide at least one seed song in the JSON.")
        return
    
    for i, seed in enumerate(seeds):
        if not isinstance(seed, dict):
            click.echo(f"Error: Seed {i+1} must be a dict with 'title', 'artist', and 'album' fields.")
            return
        
        if not all(k in seed for k in ['title', 'artist', 'album']):
            click.echo(f"Error: Seed {i+1} missing required fields. Need 'title', 'artist', and 'album'.")
            click.echo(f"Got: {seed}")
            return

    try:
        with MusicDatabase(cfg) as db:
            similarity_index = SimilarityIndex(cfg)
            similarity_index.load()
            
            generator = PlaylistGenerator(cfg, db, similarity_index)
            exporter = PlaylistExporter(cfg)
            
            pl = generator.generate(seeds, length=length, bpm_jitter_percent=bpm_jitter)
            
            if pl:
                exporter.export(pl, output, format=format)
                click.echo(f"Playlist ({len(pl)} songs) saved to {output}")
                
                if sync_to_navidrome:
                    _sync_to_navidrome(
                        pl, cfg, output, playlist_name,
                        navidrome_url, navidrome_username, navidrome_password
                    )
            else:
                click.echo("Error: Could not generate playlist")
    except Exception as e:
        click.echo(f"Error: {e}")


def _sync_to_navidrome(
    playlist,
    config: Config,
    output_path: str,
    playlist_name: str = None,
    navidrome_url: str = None,
    navidrome_username: str = None,
    navidrome_password: str = None
) -> None:
    """
    Sync a generated playlist to Navidrome server.
    
    Args:
        playlist: Generated Playlist object
        config: Config object
        output_path: Path to the output M3U file
        playlist_name: Name for the playlist (optional)
        navidrome_url: Navidrome server URL (optional)
        navidrome_username: Navidrome username (optional)
        navidrome_password: Navidrome password (optional)
    """
    url = navidrome_url or os.getenv('NAVIDROME_URL') or config.navidrome_url
    username = navidrome_username or os.getenv('NAVIDROME_USERNAME') or config.navidrome_username
    password = navidrome_password or os.getenv('NAVIDROME_PASSWORD') or config.navidrome_password
    
    if not all([url, username, password]):
        click.echo("Warning: Navidrome sync enabled but credentials not provided.")
        click.echo("Provide via --navidrome-* flags, environment variables, or config file.")
        return
    
    if not playlist_name:
        playlist_name = Path(output_path).stem
    
    try:
        click.echo(f"Syncing playlist to Navidrome at {url}...")
        
        client = NavidromeClient(url, username, password)
        
        song_ids = []
        matched_count = 0
        skipped_songs = []
        
        for song in playlist.songs:
            song_id = client.search_song(
                title=song.title,
                artist=song.artist,
                album=song.album
            )
            
            if song_id:
                song_ids.append(song_id)
                matched_count += 1
            else:
                skipped_songs.append(f"{song.title} by {song.artist}")
        
        if not song_ids:
            click.echo("Error: No songs could be matched on Navidrome. Sync aborted.")
            return
        
        if skipped_songs:
            click.echo(f"Warning: {len(skipped_songs)} song(s) could not be matched:")
            for skipped in skipped_songs[:5]:
                click.echo(f"  - {skipped}")
            if len(skipped_songs) > 5:
                click.echo(f"  ... and {len(skipped_songs) - 5} more")
        
        existing_playlist = client.get_playlist_by_name(playlist_name)
        
        if existing_playlist:
            playlist_id = existing_playlist['id']
            click.echo(f"Updating existing playlist '{playlist_name}' (ID: {playlist_id})...")
            
            if client.replace_playlist_songs(playlist_id, song_ids):
                click.echo(f"✓ Playlist '{playlist_name}' successfully updated on Navidrome")
                click.echo(f"  Matched: {matched_count}/{len(playlist.songs)} songs")
            else:
                click.echo(f"Error: Failed to update playlist '{playlist_name}'")
        else:
            click.echo(f"Creating new playlist '{playlist_name}'...")
            
            playlist_id = client.create_playlist(playlist_name, song_ids)
            
            if playlist_id:
                click.echo(f"✓ Playlist '{playlist_name}' successfully created on Navidrome (ID: {playlist_id})")
                click.echo(f"  Matched: {matched_count}/{len(playlist.songs)} songs")
            else:
                click.echo(f"Error: Failed to create playlist '{playlist_name}'")
    
    except Exception as e:
        click.echo(f"Error syncing to Navidrome: {e}")
        logger.exception("Navidrome sync failed")


if __name__ == "__main__":
    cli()
