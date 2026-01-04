# Vibe-DJ

A music library indexer and intelligent playlist generator using audio feature analysis and similarity search.

## Overview

Vibe-DJ analyzes your music library, extracts audio features using librosa, and generates playlists based on similarity to seed songs. It uses FAISS for efficient similarity search and supports BPM-based sorting for smooth transitions.

## Architecture

The codebase follows **Object-Oriented Programming (OOP) best practices** with clear separation of concerns:

### Data Models (`src/vibe_dj/models/`)

- **`Song`**: Represents a music track with metadata (title, artist, album, genre, file path, etc.)
- **`Features`**: Audio feature vector and BPM extracted from a song
- **`Playlist`**: Collection of songs with seed song tracking
- **`Config`**: Application configuration with sensible defaults

### Core Components (`src/vibe_dj/core/`)

- **`MusicDatabase`**: Database operations for songs and features
  - Context manager support for automatic connection handling
  - CRUD operations for songs and features
  - Query methods for finding songs by various criteria

- **`AudioAnalyzer`**: Audio feature extraction
  - Extracts MFCC, chroma, tempo, loudness, spectral features
  - Metadata extraction from audio files
  - MusicBrainz integration for enhanced metadata

- **`SimilarityIndex`**: FAISS-based similarity search
  - Build and maintain vector similarity index
  - Efficient k-nearest neighbor search
  - Add/remove vectors dynamically

- **`LibraryIndexer`**: Music library scanning and indexing
  - Multi-phase processing (metadata → features → database)
  - Parallel processing with threading (adaptive worker count)
  - Incremental updates (only processes new/modified files)
  - Progress tracking with tqdm
  - Timeout handling for problematic files

### Services (`src/vibe_dj/services/`)

- **`PlaylistGenerator`**: Intelligent playlist generation
  - Find seed songs by exact match (title, artist, album)
  - Compute average feature vector from seeds
  - Query vector perturbation for variety across runs
  - Expanded candidate pool with random sampling
  - Find similar songs using similarity index
  - BPM-based sorting with configurable jitter

- **`PlaylistExporter`**: Export playlists to various formats
  - M3U/M3U8 format support
  - JSON export with full metadata
  - Extensible for additional formats

## Installation

### Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd vibe-dj

# Install dependencies
uv sync

# Or with pip
pip install -e .
```

### Docker Installation

```bash
# Clone the repository
git clone <repository-url>
cd vibe-dj

# Build the Docker image
docker build -t vibe-dj .

# Or use docker-compose
docker-compose build
```

## Usage

### Using Docker

The Docker container is designed to run the CLI with your music library mounted as an external volume. All persistent data (database, FAISS index, playlists) is stored in a `/data` directory that should be mounted as a volume.

#### Quick Start (Docker)

```bash
# 1. Build the image
docker build -t vibe-dj .

# 2. Create a data directory
mkdir -p data

# 3. Index your music library
docker run --rm \
  -v /path/to/your/music:/music:ro \
  -v $(pwd)/data:/data \
  vibe-dj index /music

# 4. Create seeds.json in the data directory
cat > data/seeds.json << 'EOF'
{
  "seeds": ["Your Song Title", "Another Song"]
}
EOF

# 5. Generate a playlist
docker run --rm \
  -v $(pwd)/data:/data \
  vibe-dj playlist --seeds-json /data/seeds.json --output /data/playlist.m3u
```

#### Basic Docker Usage

**Index your music library:**
```bash
docker run --rm \
  -v /path/to/your/music:/music:ro \
  -v $(pwd)/data:/data \
  vibe-dj index /music
```

**Generate a playlist:**

First, create a `seeds.json` file in your `data` directory:
```json
{
  "seeds": [
    {
      "title": "Song Title 1",
      "artist": "Artist Name 1",
      "album": "Album Name 1"
    },
    {
      "title": "Song Title 2",
      "artist": "Artist Name 2",
      "album": "Album Name 2"
    }
  ]
}
```

Then run:
```bash
docker run --rm \
  -v /path/to/your/music:/music:ro \
  -v $(pwd)/data:/data \
  vibe-dj playlist --seeds-json /data/seeds.json --output /data/playlist.m3u
```

#### Using Docker Compose

Edit `docker-compose.yml` to set your music library path:
```yaml
volumes:
  - /path/to/your/music:/music:ro
  - ./data:/data
```

Then run commands:
```bash
# Index library
docker-compose run --rm vibe-dj index /music

# Generate playlist (with seeds.json in ./data/)
docker-compose run --rm vibe-dj playlist --seeds-json /data/seeds.json --output /data/playlist.m3u
```

#### Docker Volume Mapping

- **`/music`**: Mount your music library here (read-only recommended with `:ro`)
- **`/data`**: Mount a local directory for persistent data:
  - `music.db` - SQLite database
  - `faiss_index.bin` - FAISS similarity index
  - `playlist.m3u` - Generated playlists
  - `seeds.json` - Seed songs configuration
  - `config.json` - Optional custom configuration

#### Docker Configuration

To use a custom config with Docker, place `config.json` in your data directory:
```bash
docker run --rm \
  -v /path/to/your/music:/music:ro \
  -v $(pwd)/data:/data \
  vibe-dj index /music --config /data/config.json
```

#### Using Makefile Targets (Docker)

For convenience, you can use the provided Makefile targets:

```bash
# Build the Docker image
make docker-build

# Index your music library
make docker-index MUSIC_PATH=/path/to/your/music

# Generate a playlist (requires data/seeds.json)
make docker-playlist

# Open a shell in the container for debugging
make docker-shell
```

### Using Locally

### Index Your Music Library

```bash
vibe-dj index /path/to/music/library
```

Options:
- `--config PATH`: Path to custom config JSON file

### Generate a Playlist

Create a seeds file (`seeds.json`):
```json
{
  "seeds": [
    {
      "title": "Song Title 1",
      "artist": "Artist Name 1",
      "album": "Album Name 1"
    },
    {
      "title": "Song Title 2",
      "artist": "Artist Name 2",
      "album": "Album Name 2"
    }
  ]
}
```

Generate playlist:
```bash
vibe-dj playlist --seeds-json seeds.json --output my_playlist.m3u
```

Options:
- `--output PATH`: Output file path (default: `playlist.m3u`)
- `--format FORMAT`: Output format: `m3u`, `m3u8`, or `json` (default: `m3u`)
- `--length N`: Number of songs in playlist (default: 20)
- `--bpm-jitter PERCENT`: BPM jitter for sorting variety (default: 5.0)
- `--config PATH`: Path to custom config JSON file

**Note:** Each time you run the playlist command with the same seeds, you'll get different but acoustically similar results due to query perturbation and random sampling.

## Configuration

Create a `config.json` file:

```json
{
  "database_path": "music.db",
  "faiss_index_path": "faiss_index.bin",
  "playlist_output": "playlist.m3u",
  "sample_rate": 22050,
  "max_duration": 180,
  "n_mfcc": 13,
  "parallel_workers": 4,
  "batch_size": 10,
  "processing_timeout": 30,
  "query_noise_scale": 0.1,
  "candidate_multiplier": 4
}
```

### Playlist Variety Parameters

- **`query_noise_scale`** (default: `0.1`): Controls how much random noise is added to the query vector. Higher values (e.g., 0.15-0.2) produce more variety but may drift from the intended vibe. Lower values (e.g., 0.05) produce more consistent results. Set to 0 to disable perturbation.

- **`candidate_multiplier`** (default: `4`): Determines how many candidate songs to fetch before random sampling. For a 20-song playlist with multiplier 4, it fetches 80 candidates and randomly selects 20. Higher values increase variety but require more computation.

## Development

### Running Tests

```bash
# Run all tests
pytest tests/unit/ -v

# Run specific test module
pytest tests/unit/models/test_song.py -v

# Run with coverage
pytest tests/unit/ --cov=vibe_dj --cov-report=html
```

### Project Structure

```
vibe-dj/
├── src/vibe_dj/
│   ├── models/          # Data models (Song, Features, Playlist, Config)
│   ├── core/            # Core components (Database, Analyzer, Indexer, Similarity)
│   ├── services/        # Services (PlaylistGenerator, PlaylistExporter)
│   └── main.py          # CLI entry point
├── tests/
│   └── unit/            # Unit tests mirroring src structure
├── data/                # Docker data directory (gitignored)
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Docker Compose configuration
├── .dockerignore        # Docker build exclusions
├── config.example.json  # Example configuration file
├── seeds.example.json   # Example seeds file
├── Makefile             # Build and Docker targets
├── pyproject.toml       # Project configuration
└── README.md
```

## Design Principles

1. **Single Responsibility**: Each class has one clear purpose
2. **Dependency Injection**: Classes receive dependencies through constructors
3. **Composition over Inheritance**: Favor composition for flexibility
4. **Context Managers**: Automatic resource management (database connections)
5. **Type Hints**: Full type annotations for better IDE support
6. **Testability**: All components are unit tested with mocks

## Features

- **Incremental Indexing**: Only processes new or modified files
- **Parallel Processing**: Multi-core audio analysis for faster indexing
- **Similarity Search**: FAISS-powered efficient similarity search
- **Playlist Variety**: Query perturbation and random sampling for different results on each run
- **BPM Sorting**: Smooth transitions with configurable jitter
- **Multiple Export Formats**: M3U, M3U8, and JSON
- **MusicBrainz Integration**: Enhanced metadata from MusicBrainz
- **Progress Tracking**: Visual progress bars for long operations
- **Configurable**: JSON-based configuration system

## Requirements

- Python >= 3.13
- librosa (audio analysis)
- faiss-cpu (similarity search)
- mutagen (metadata extraction)
- musicbrainzngs (MusicBrainz API)
- click (CLI framework)
- tqdm (progress bars)
- loguru (logging)

## License

See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

## Troubleshooting

### Indexing is slow
- Adjust `parallel_workers` in config (default: 4)
- Reduce `max_duration` to analyze less of each song

### Out of memory during indexing
- Reduce `parallel_workers`
- Reduce `max_duration`

### No similar songs found
- Check that the FAISS index was built successfully
- Verify seed song title, artist, and album match database entries exactly
- Try different seed songs
- Use `sqlite3 music.db "SELECT title, artist, album FROM songs LIMIT 10;"` to see available songs

### Playlists are too similar/different between runs
- Adjust `query_noise_scale` in config (lower for more consistency, higher for more variety)
- Adjust `candidate_multiplier` (higher values increase variety)
- Set `query_noise_scale` to 0 for completely deterministic results

### Docker: Permission denied errors
- Ensure the `data` directory has proper permissions
- On Linux, you may need to run: `chmod -R 777 data/`
- Or run the container with your user ID: `docker run --user $(id -u):$(id -g) ...`

### Docker: Cannot find music files
- Verify the music path is correctly mounted: `-v /absolute/path/to/music:/music:ro`
- Check that the path inside the container is `/music` in your commands
- Ensure the music directory contains supported audio files

### Docker: Database or index not persisting
- Ensure the data directory is mounted: `-v $(pwd)/data:/data`
- Check that files are being created in the mounted `data/` directory
- Verify the container has write permissions to the data directory
