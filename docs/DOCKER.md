# Docker Guide for Vibe-DJ

This guide provides detailed instructions for running Vibe-DJ in a Docker container.

## Quick Start

```bash
# Build the image
docker build -t vibe-dj .

# Create data directory
mkdir -p data

# Index your music
docker run --rm \
  -v /path/to/your/music:/music:ro \
  -v $(pwd)/data:/data \
  vibe-dj index /music

# Create seeds file
cp seeds.example.json data/seeds.json
# Edit data/seeds.json with your song titles

# Generate playlist
docker run --rm \
  -v $(pwd)/data:/data \
  vibe-dj playlist --seeds-json /data/seeds.json --output /data/playlist.m3u
```

## Architecture

The Docker setup uses two volume mounts:

1. **`/music`** - Your music library (read-only)
2. **`/data`** - Persistent data directory containing:
   - `music.db` - SQLite database with song metadata
   - `faiss_index.bin` - FAISS similarity index
   - `playlist.m3u` - Generated playlists
   - `seeds.json` - Seed songs configuration
   - `config.json` - Optional custom configuration

## Docker Commands

### Build

```bash
# Build from Dockerfile
docker build -t vibe-dj .

# Build with docker-compose
docker-compose build
```

### Index Music Library

```bash
# Basic indexing
docker run --rm \
  -v /path/to/music:/music:ro \
  -v $(pwd)/data:/data \
  vibe-dj index /music

# With custom config
docker run --rm \
  -v /path/to/music:/music:ro \
  -v $(pwd)/data:/data \
  vibe-dj index /music --config /data/config.json
```

### Generate Playlists

```bash
# Basic playlist generation
docker run --rm \
  -v $(pwd)/data:/data \
  vibe-dj playlist \
    --seeds-json /data/seeds.json \
    --output /data/playlist.m3u

# With options
docker run --rm \
  -v $(pwd)/data:/data \
  vibe-dj playlist \
    --seeds-json /data/seeds.json \
    --output /data/my_mix.m3u \
    --length 50 \
    --bpm-jitter 10.0 \
    --format m3u8
```

## Docker Compose

Edit `docker-compose.yml` to set your music path:

```yaml
volumes:
  - /your/actual/music/path:/music:ro
  - ./data:/data
```

Then use:

```bash
# Index
docker-compose run --rm vibe-dj index /music

# Generate playlist
docker-compose run --rm vibe-dj playlist \
  --seeds-json /data/seeds.json \
  --output /data/playlist.m3u
```

## Makefile Targets

```bash
# Build image
make docker-build

# Index music (requires MUSIC_PATH variable)
make docker-index MUSIC_PATH=/path/to/music

# Generate playlist (uses data/seeds.json)
make docker-playlist

# Debug shell
make docker-shell
```

## Configuration

### Custom Config File

Create `data/config.json`:

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

Use it:

```bash
docker run --rm \
  -v /path/to/music:/music:ro \
  -v $(pwd)/data:/data \
  vibe-dj index /music --config /data/config.json
```

### Seeds File

Create `data/seeds.json`:

```json
{
  "seeds": [
    "Exact Song Title 1",
    "Exact Song Title 2",
    "Another Song Title"
  ]
}
```

## Troubleshooting

### Permission Issues (Linux)

If you encounter permission errors:

```bash
# Option 1: Run as your user
docker run --rm --user $(id -u):$(id -g) \
  -v /path/to/music:/music:ro \
  -v $(pwd)/data:/data \
  vibe-dj index /music

# Option 2: Fix permissions
chmod -R 777 data/
```

### Music Files Not Found

- Use absolute paths for volume mounts
- Verify the mount with: `docker run --rm -v /path/to/music:/music:ro vibe-dj ls /music`
- Ensure supported audio formats (MP3, FLAC, WAV, etc.)

### Data Not Persisting

- Always mount the data directory: `-v $(pwd)/data:/data`
- Check that `data/` exists before running
- Verify files appear in local `data/` directory after indexing

### Debugging

Open a shell in the container:

```bash
docker run --rm -it \
  -v $(pwd)/data:/data \
  --entrypoint /bin/bash \
  vibe-dj

# Inside container, you can run commands manually:
# vibe-dj --help
# ls -la /data
# cat /data/config.json
```

## Performance Tuning

### For Large Libraries

Create `data/config.json`:

```json
{
  "parallel_workers": 8,
  "batch_size": 20,
  "max_duration": 120,
  "processing_timeout": 60
}
```

### For Low-Memory Systems

```json
{
  "parallel_workers": 2,
  "batch_size": 5,
  "max_duration": 60
}
```

## Best Practices

1. **Mount music as read-only** (`:ro`) to prevent accidental modifications
2. **Use absolute paths** for volume mounts
3. **Keep data directory** outside the container for persistence
4. **Backup database** before major re-indexing: `cp data/music.db data/music.db.backup`
5. **Use docker-compose** for consistent configuration
6. **Version your seeds files** for different playlist styles

## Examples

### Multiple Playlists

```bash
# Chill playlist
cat > data/seeds_chill.json << 'EOF'
{"seeds": ["Ambient Song 1", "Downtempo Track"]}
EOF

docker run --rm -v $(pwd)/data:/data vibe-dj playlist \
  --seeds-json /data/seeds_chill.json \
  --output /data/chill_mix.m3u \
  --length 30

# Workout playlist
cat > data/seeds_workout.json << 'EOF'
{"seeds": ["High Energy Song", "Fast Beat Track"]}
EOF

docker run --rm -v $(pwd)/data:/data vibe-dj playlist \
  --seeds-json /data/seeds_workout.json \
  --output /data/workout_mix.m3u \
  --length 40 \
  --bpm-jitter 2.0
```

### Incremental Updates

```bash
# Initial index
docker run --rm \
  -v /path/to/music:/music:ro \
  -v $(pwd)/data:/data \
  vibe-dj index /music

# Later, after adding new music (only new files are processed)
docker run --rm \
  -v /path/to/music:/music:ro \
  -v $(pwd)/data:/data \
  vibe-dj index /music
```

## System Requirements

- Docker 20.10+
- 2GB+ RAM (4GB+ recommended for large libraries)
- Disk space for data directory (varies by library size)
- Supported audio formats in music library

## Support

For issues, see the main README.md troubleshooting section or open an issue on the repository.
