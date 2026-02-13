import json
from pathlib import Path

import click

from .core import AudioAnalyzer, LibraryIndexer, MusicDatabase, SimilarityIndex
from .models import Config
from .services import NavidromeSyncService, PlaylistExporter, PlaylistGenerator


@click.group()
def cli():
    """Vibe-DJ: AI-powered music playlist generator.

    Command-line interface for indexing music libraries and generating
    playlists based on audio similarity.
    """
    pass


@cli.command()
@click.argument("library_path")
@click.option("--config", type=click.Path(exists=True), help="Path to config JSON file")
def index(library_path, config):
    """Index the music library at LIBRARY_PATH.

    Scans the specified directory for audio files, extracts metadata and
    audio features, and builds a similarity index for playlist generation.

    :param library_path: Path to the music library directory
    :param config: Optional path to configuration JSON file
    """
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
@click.option(
    "--seeds-json",
    type=click.Path(exists=True),
    required=True,
    help='JSON file with seeds: {"seeds": [{"title": "...", "artist": "...", "album": "..."}]}',
)
@click.option(
    "--output", type=click.Path(), default=None, help="Output playlist file path"
)
@click.option(
    "--format",
    type=click.Choice(["m3u", "m3u8", "json"], case_sensitive=False),
    default="m3u",
    help="Output format (default: m3u)",
)
@click.option(
    "--length", type=int, default=20, help="Number of songs in playlist (default: 20)"
)
@click.option(
    "--bpm-jitter",
    type=float,
    default=5.0,
    help="BPM jitter percentage for sorting (default: 5.0)",
)
@click.option("--config", type=click.Path(exists=True), help="Path to config JSON file")
@click.option(
    "--sync-to-navidrome",
    is_flag=True,
    default=False,
    help="Sync playlist to Navidrome server",
)
@click.option(
    "--navidrome-url",
    type=str,
    default=None,
    help="Navidrome server URL (e.g., http://192.168.1.100:4533)",
)
@click.option("--navidrome-username", type=str, default=None, help="Navidrome username")
@click.option("--navidrome-password", type=str, default=None, help="Navidrome password")
@click.option(
    "--playlist-name",
    type=str,
    default=None,
    help="Name for the playlist on Navidrome (defaults to output filename)",
)
def playlist(
    seeds_json,
    output,
    format,
    length,
    bpm_jitter,
    config,
    sync_to_navidrome,
    navidrome_url,
    navidrome_username,
    navidrome_password,
    playlist_name,
):
    """Generate a playlist from seed songs.

    Creates a playlist of similar songs based on seed tracks. Each seed
    requires title, artist, and album fields for accurate matching.
    Optionally syncs the generated playlist to a Navidrome server.

    :param seeds_json: Path to JSON file containing seed songs
    :param output: Output file path for the playlist
    :param format: Export format (m3u, m3u8, or json)
    :param length: Number of songs to generate
    :param bpm_jitter: BPM jitter percentage for sorting
    :param config: Optional path to configuration JSON file
    :param sync_to_navidrome: Flag to enable Navidrome sync
    :param navidrome_url: Navidrome server URL
    :param navidrome_username: Navidrome username
    :param navidrome_password: Navidrome password
    :param playlist_name: Name for the playlist on Navidrome
    """
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
            click.echo(
                f"Error: Seed {i + 1} must be a dict with 'title', 'artist', and 'album' fields."
            )
            return

        if not all(k in seed for k in ["title", "artist", "album"]):
            click.echo(
                f"Error: Seed {i + 1} missing required fields. Need 'title', 'artist', and 'album'."
            )
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
                exporter.export(pl, output, output_format=format)
                click.echo(f"Playlist ({len(pl)} songs) saved to {output}")

                if sync_to_navidrome:
                    sync_service = NavidromeSyncService(cfg)
                    resolved_playlist_name = playlist_name or Path(output).stem
                    result = sync_service.sync_playlist(
                        pl,
                        resolved_playlist_name,
                        navidrome_url,
                        navidrome_username,
                        navidrome_password,
                    )

                    if result["success"]:
                        click.echo(
                            f"✓ Playlist '{result['playlist_name']}' successfully {result['action']} on Navidrome"
                        )
                        click.echo(
                            f"  Matched: {result['matched_count']}/{result['total_count']} songs"
                        )

                        if result["skipped_songs"]:
                            click.echo(
                                f"  Warning: {len(result['skipped_songs'])} song(s) could not be matched:"
                            )
                            for skipped in result["skipped_songs"][:5]:
                                click.echo(f"    - {skipped}")
                            if len(result["skipped_songs"]) > 5:
                                click.echo(
                                    f"    ... and {len(result['skipped_songs']) - 5} more"
                                )
                    else:
                        click.echo("Error: Failed to sync playlist to Navidrome")
                        if result["error"]:
                            click.echo(f"  Reason: {result['error']}")
            else:
                click.echo("Error: Could not generate playlist")
    except Exception as e:
        click.echo(f"Error: {e}")


if __name__ == "__main__":
    cli()
