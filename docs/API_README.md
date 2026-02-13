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

Configuration is provided via:

**Config file** (`config.json` in working directory)

**Defaults**

### Example config.json

```json
{
  "database_path": "music.db",
  "faiss_index_path": "faiss_index.bin",
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
