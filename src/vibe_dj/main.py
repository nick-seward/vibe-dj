import click
import json
from .indexer import index_library
from .playlist_gen import generate_playlist
from .config import PLAYLIST_OUTPUT

@click.group()
def cli():
    pass

@cli.command()
@click.argument("library_path")
def index(library_path):
    """Index the music library at LIBRARY_PATH."""
    index_library(library_path)

@cli.command()
@click.option("--seeds-json", type=click.Path(exists=True), required=True,
              help='JSON file like {"seeds": ["Song Title One", "Another Song"]}')
@click.option("--output", type=click.Path(), default=PLAYLIST_OUTPUT,
              help="Output M3U file path")
def playlist(seeds_json, output):
    """Generate a 20-song playlist from seed titles."""
    with open(seeds_json) as f:
        data = json.load(f)
        seeds = data["seeds"]

    if not 1 <= len(seeds) <= 2:
        click.echo("Provide 1 or 2 seed songs in the JSON.")
        return

    try:
        pl = generate_playlist(seeds, output_path=output)
        click.echo(f"Playlist ({len(pl)} songs) saved to {output}")
    except Exception as e:
        click.echo(f"Error: {e}")

if __name__ == "__main__":
    cli()
