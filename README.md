# Vibe-DJ

A music library indexer and intelligent playlist generator using audio feature analysis and similarity search.

## Overview

Vibe-DJ analyzes your music library, extracts audio features using librosa, and generates playlists based on similarity to seed songs. It uses FAISS for efficient similarity search and supports BPM-based sorting for smooth transitions.


## Development

### Prerequisites

- Python 3.14
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Node v24](https://nodejs.org/en/download)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd vibe-dj

# Setup virtual environment
uv venv

# Install dependencies
make install

# Run unit tests
make test

# Start server - Accessible at http://localhost:8000
make run

# You can run the API and UI servers separately
# Start API server - Accessible at http://localhost:8000
make api-server

# Start UI development server - Accessible at http://localhost:5173
make ui-server
```

## Docker

### Building the Docker Image

```bash
./build-docker.sh Dockerfile-server vibe-dj
```

## How It Works

When `--sync-to-navidrome` is enabled:

1. **Local playlist is generated** and saved to M3U file (always happens first)
2. **Songs are matched** on Navidrome using a three-tier search strategy:
   - Primary: Search by title + artist + album (most accurate)
   - Fallback 1: Search by title + artist
   - Fallback 2: Search by title only
3. **Playlist is created or updated**:
   - If a playlist with the same name exists, it's updated with new songs
   - If not, a new playlist is created
4. **Results are reported**: Shows matched songs and any that couldn't be found

#### Song Matching

The sync process uses intelligent song matching to find your local tracks on Navidrome:

- **Best match**: Uses all available metadata (title, artist, album)
- **Fallback matching**: Tries progressively simpler searches if exact match fails
- **Skips gracefully**: Songs that can't be matched are skipped with warnings
- **Continues on errors**: Local M3U file is always created, even if Navidrome sync fails

**Note**: Song matching accuracy depends on metadata consistency between your local library and Navidrome. Ensure your music files have proper ID3 tags for best results.

#### Playlist Updates

If you run the command again with the same `--playlist-name`, the existing playlist on Navidrome will be updated with the new song list. This allows you to:

- Regenerate playlists with the same seeds (getting new variety)
- Update playlists with different parameters (length, BPM jitter)
- Keep playlist names consistent across regenerations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request
