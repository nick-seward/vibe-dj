# Vibe-DJ

A music library indexer and intelligent playlist generator using audio feature analysis and similarity search.

## Overview

Vibe-DJ analyzes your music library, extracts audio features using librosa, and generates playlists based on similarity to seed songs. It uses FAISS for efficient similarity search and supports BPM-based sorting for smooth transitions.

## Architecture

The codebase follows **Object-Oriented Programming (OOP) best practices** with clear separation of concerns:

### Data Models (`src/vibe_dj/models/`)

- **`Song`**: Represents a music track with metadata (title, artist, genre, file path, etc.)
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
  - Find seed songs by title
  - Compute average feature vector from seeds
  - Find similar songs using similarity index
  - BPM-based sorting with configurable jitter

- **`PlaylistExporter`**: Export playlists to various formats
  - M3U/M3U8 format support
  - JSON export with full metadata
  - Extensible for additional formats

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd vibe-dj

# Install dependencies
uv sync

# Or with pip
pip install -e .
```

## Usage

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
  "seeds": ["Song Title 1", "Song Title 2"]
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
  "processing_timeout": 30
}
```

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
- Verify seed song titles match database entries
- Try different seed songs
