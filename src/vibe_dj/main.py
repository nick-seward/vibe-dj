import click
import json
from .models import Config
from .core import MusicDatabase, AudioAnalyzer, SimilarityIndex, LibraryIndexer
from .services import PlaylistGenerator, PlaylistExporter


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
def playlist(seeds_json, output, format, length, bpm_jitter, config):
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
            else:
                click.echo("Error: Could not generate playlist")
    except Exception as e:
        click.echo(f"Error: {e}")


if __name__ == "__main__":
    cli()
