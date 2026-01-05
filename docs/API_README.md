# Vibe-DJ FastAPI Backend

The Vibe-DJ API provides REST endpoints for music library indexing and intelligent playlist generation using audio feature analysis and FAISS similarity search.

## Quick Start

### Running Locally

```bash
# Install dependencies
uv sync

# Start the API server
uvicorn vibe_dj.app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Running with Docker

```bash
# Build the API container
docker build -f Dockerfile-API -t vibe-dj-api .

# Run the API server
docker run -p 8000:8000 \
  -v $(pwd)/data:/data \
  -v /path/to/music:/music:ro \
  vibe-dj-api
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Endpoints

### Health & Info

#### `GET /`
Root endpoint with API information.

**Response:**
```json
{
  "name": "Vibe-DJ API",
  "version": "0.1.0",
  "description": "Music library indexer and intelligent playlist generator",
  "endpoints": {
    "docs": "/docs",
    "health": "/health",
    "index": "/api/index",
    "status": "/api/status/{job_id}",
    "playlist": "/api/playlist",
    "songs": "/api/songs"
  }
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "faiss_index": "available"
}
```

### Indexing

#### `POST /api/index`
Trigger library indexing as a background task.

**Request:**
```json
{
  "library_path": "/path/to/music",
  "config_overrides": {
    "parallel_workers": 8,
    "batch_size": 20
  }
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Indexing job queued for /path/to/music"
}
```

#### `POST /api/index/upload`
Trigger library indexing with optional config file upload.

**Form Data:**
- `library_path` (string, required): Path to music library
- `config_file` (file, optional): JSON configuration file

**Response:** Same as `/api/index`

#### `GET /api/status/{job_id}`
Get status of a background indexing job.

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress": {
    "phase": "scanning",
    "message": "Scanning music library..."
  },
  "error": null,
  "started_at": "2026-01-04T12:00:00",
  "completed_at": null
}
```

**Status values:** `queued`, `running`, `completed`, `failed`

### Playlist Generation

#### `POST /api/playlist`
Generate a playlist from seed songs.

**Request:**
```json
{
  "seeds": [
    {
      "title": "Song Title",
      "artist": "Artist Name",
      "album": "Album Name"
    }
  ],
  "length": 20,
  "bpm_jitter": 5.0,
  "format": "json",
  "sync_to_navidrome": false,
  "navidrome_config": {
    "url": "http://navidrome:4533",
    "username": "admin",
    "password": "password",
    "playlist_name": "My Playlist"
  }
}
```

**Response:**
```json
{
  "songs": [
    {
      "id": 1,
      "file_path": "/music/song.mp3",
      "title": "Song Title",
      "artist": "Artist Name",
      "album": "Album Name",
      "genre": "Rock",
      "duration": 180,
      "last_modified": 1234567890.0
    }
  ],
  "seed_songs": [...],
  "created_at": "2026-01-04T12:00:00",
  "length": 20
}
```

#### `POST /api/playlist/download`
Generate a playlist and download as a file.

**Request:** Same as `/api/playlist`

**Response:** File download (M3U, M3U8, or JSON)

#### `POST /api/export`
Export a list of songs to a playlist file.

**Request:**
```json
{
  "song_ids": [1, 2, 3],
  "format": "m3u",
  "output_path": "/data/playlist.m3u"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Playlist exported to /data/playlist.m3u",
  "song_count": 3
}
```

### Songs

#### `GET /api/songs`
List songs with pagination and optional search.

**Query Parameters:**
- `limit` (int, default: 100): Maximum number of songs to return
- `offset` (int, default: 0): Number of songs to skip
- `search` (string, optional): Search query for title, artist, or album

**Response:**
```json
{
  "songs": [...],
  "total": 1000,
  "limit": 100,
  "offset": 0
}
```

#### `GET /api/songs/{song_id}`
Get detailed information about a specific song.

**Response:**
```json
{
  "song": {
    "id": 1,
    "file_path": "/music/song.mp3",
    "title": "Song Title",
    "artist": "Artist Name",
    "album": "Album Name",
    "genre": "Rock",
    "duration": 180,
    "last_modified": 1234567890.0
  },
  "features": {
    "song_id": 1,
    "bpm": 120.0,
    "feature_vector_length": 128
  }
}
```

## Configuration

Configuration can be provided via:

1. **Environment variables** (highest priority):
   - `VIBE_DJ_CONFIG_PATH`: Path to config file
   - `VIBE_DJ_DATABASE_PATH`: Database file path
   - `VIBE_DJ_FAISS_INDEX_PATH`: FAISS index file path
   - `NAVIDROME_URL`: Navidrome server URL
   - `NAVIDROME_USERNAME`: Navidrome username
   - `NAVIDROME_PASSWORD`: Navidrome password

2. **Config file** (`config.json` in working directory)

3. **Defaults**

### Example config.json

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

## Error Handling

The API uses standard HTTP status codes:

- **200 OK**: Successful request
- **400 Bad Request**: Invalid input (e.g., invalid seeds, missing fields)
- **404 Not Found**: Resource not found (e.g., song ID, job ID)
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable (e.g., FAISS index not loaded)

Error responses include details:

```json
{
  "error": "Error message",
  "status_code": 400
}
```

## Testing

Run the API tests:

```bash
# Run all API tests
uv run pytest tests/test_api.py -v

# Run with coverage
uv run pytest tests/test_api.py --cov=vibe_dj.api --cov=vibe_dj.app --cov-report=html
```

## Architecture

### Components

- **`app.py`**: FastAPI application entrypoint with CORS and error handling
- **`api/models.py`**: Pydantic request/response models
- **`api/dependencies.py`**: Dependency injection (database, config, services)
- **`api/background.py`**: Background job manager for long-running tasks
- **`api/routes/`**: Route handlers organized by domain
  - `index.py`: Indexing endpoints
  - `playlist.py`: Playlist generation and export
  - `songs.py`: Song listing and retrieval

### Design Principles

- **Dependency Injection**: Services injected via FastAPI's `Depends()`
- **Background Tasks**: Long-running indexing uses `BackgroundTasks`
- **Type Safety**: Full Pydantic validation on all inputs/outputs
- **Error Handling**: Consistent HTTPException usage with proper status codes
- **Separation of Concerns**: Routes delegate to existing services
- **Backward Compatibility**: CLI (`main.py`) remains functional

## Deployment

### Docker Compose Example

```yaml
version: '3.8'

services:
  vibe-dj-api:
    build:
      context: .
      dockerfile: Dockerfile-API
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
      - /path/to/music:/music:ro
    environment:
      - VIBE_DJ_DATABASE_PATH=/data/music.db
      - VIBE_DJ_FAISS_INDEX_PATH=/data/faiss_index.bin
    restart: unless-stopped
```

### Production Considerations

1. **Authentication**: Add API key authentication for production
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Job Persistence**: Use Redis for job tracking in multi-instance deployments
4. **HTTPS**: Use reverse proxy (nginx/traefik) with SSL certificates
5. **Monitoring**: Add logging, metrics, and health checks
6. **Scaling**: Use multiple workers with shared database and FAISS index

## CLI Compatibility

The original CLI remains fully functional:

```bash
# Index library (CLI)
vibe-dj index /path/to/music

# Generate playlist (CLI)
vibe-dj playlist --seeds-json seeds.json --output playlist.m3u
```

Both CLI and API share the same core services and database.
