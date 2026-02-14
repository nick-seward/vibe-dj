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

Two Dockerfiles are provided:

- **`Dockerfile`** — API-only image (no UI)
- **`Dockerfile-Server`** — Full server with React UI (recommended for production)

### Building the Docker Image

```bash
# Full server with UI (recommended)
./build-docker.sh Dockerfile-Server vibe-dj-server

# API-only
./build-docker.sh Dockerfile vibe-dj
```

## How It Works

1. **Index your library** via the web UI settings page — scans audio files and extracts features
2. **Search for songs** to use as seeds for playlist generation
3. **Generate a playlist** — the API finds similar songs using FAISS and sorts by BPM
4. **Optionally sync to Navidrome** — push the generated playlist to a Navidrome/Subsonic server

### Navidrome Sync

When syncing a playlist to Navidrome, songs are matched using a three-tier search strategy:

- **Primary**: Search by title + artist + album (most accurate)
- **Fallback 1**: Search by title + artist
- **Fallback 2**: Search by title only

If a playlist with the same name already exists on Navidrome, it is updated with the new song list. Songs that cannot be matched are skipped gracefully.

**Note**: Song matching accuracy depends on metadata consistency between your local library and Navidrome. Ensure your music files have proper ID3 tags for best results.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request
