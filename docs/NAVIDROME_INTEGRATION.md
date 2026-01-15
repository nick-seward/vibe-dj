# Navidrome Integration

## Overview

Vibe-DJ now supports automatic playlist synchronization to Navidrome servers using the Subsonic API. When enabled, generated playlists are automatically uploaded to your Navidrome server, making them instantly available in any Subsonic-compatible music player (Amperfy, Ultrasonic, etc.).

## Features

- **Automatic sync**: Playlists are synced to Navidrome after local M3U generation
- **Intelligent song matching**: Three-tier search strategy (title+artist+album → title+artist → title)
- **Playlist updates**: Existing playlists are updated rather than duplicated
- **Resilient**: Local M3U always created even if Navidrome sync fails
- **Flexible configuration**: CLI flags, environment variables, or config file
- **Secure authentication**: Uses Subsonic token/salt authentication
- **Retry logic**: Automatic retries with exponential backoff for transient failures

## Architecture

### New Components

1. **NavidromeClient** (`src/vibe_dj/services/navidrome_client.py`)
   - Subsonic API 1.16.1 client
   - Token-based authentication
   - Song search with fallback strategies
   - Playlist CRUD operations
   - Retry logic with exponential backoff

2. **Config Extensions** (`src/vibe_dj/models/config.py`)
   - `navidrome_url`: Server URL
   - `navidrome_username`: Username
   - `navidrome_password`: Password

3. **CLI Extensions** (`src/vibe_dj/main.py`)
   - `--sync-to-navidrome`: Enable sync flag
   - `--navidrome-url`: Server URL override
   - `--navidrome-username`: Username override
   - `--navidrome-password`: Password override
   - `--playlist-name`: Custom playlist name

4. **Sync Workflow** (`_sync_to_navidrome()` in `main.py`)
   - Credential resolution (CLI → env → config)
   - Song matching with progress reporting
   - Playlist creation or update
   - Error handling and user feedback

## Usage Examples

### Basic Usage

```bash
vibe-dj playlist --seeds-json seeds.json \
  --sync-to-navidrome \
  --navidrome-url http://192.168.1.100:4533 \
  --navidrome-username admin \
  --navidrome-password mypass
```

### With Environment Variables

```bash
export NAVIDROME_URL="http://192.168.1.100:4533"
export NAVIDROME_USERNAME="admin"
export NAVIDROME_PASSWORD="mypass"

vibe-dj playlist --seeds-json seeds.json --sync-to-navidrome
```

### With Config File

```json
{
  "navidrome_url": "http://192.168.1.100:4533",
  "navidrome_username": "admin",
  "navidrome_password": "mypass"
}
```

```bash
vibe-dj playlist --seeds-json seeds.json --config config.json --sync-to-navidrome
```

### Custom Playlist Name

```bash
vibe-dj playlist --seeds-json seeds.json \
  --sync-to-navidrome \
  --playlist-name "VibeDJ – Chill Evening Mix"
```

## Song Matching Strategy

The sync process uses a three-tier fallback strategy to match songs:

1. **Primary**: `title + artist + album`
   - Most accurate matching
   - Recommended for best results

2. **Fallback 1**: `title + artist`
   - Used if primary search returns no results
   - Good for cases where album metadata differs

3. **Fallback 2**: `title` only
   - Last resort
   - Least reliable but better than skipping

Songs that can't be matched at any level are skipped with warnings.

## Error Handling

- **Authentication failures**: Clear error messages with credential check
- **Network errors**: Automatic retries (3 attempts with exponential backoff)
- **Song matching failures**: Warnings logged, sync continues
- **API errors**: Detailed error messages from Subsonic API
- **Playlist conflicts**: Existing playlists updated, not duplicated

## Testing

Comprehensive unit tests in `tests/unit/services/test_navidrome_client.py`:

- Authentication token generation
- API call success and error handling
- Retry logic with transient failures
- Song search with all fallback strategies
- Playlist CRUD operations
- Edge cases (empty playlists, single results, etc.)

Run tests:
```bash
pytest tests/unit/services/test_navidrome_client.py -v
```

## Security Considerations

- **Token authentication**: Uses MD5(password + salt) instead of plain password in API calls
- **No credential logging**: Passwords/tokens never logged
- **Environment variables**: Supports env vars to avoid hardcoding credentials
- **Config file security**: Users responsible for securing config files with credentials

## Performance

- **Parallel song matching**: Could be optimized with concurrent requests (future enhancement)
- **Caching**: No caching currently (each run performs fresh searches)
- **Timeout**: 10-second timeout per API request
- **Retry delays**: 1s, 2s, 4s exponential backoff

## Future Enhancements

Potential improvements:

1. **Batch operations**: Use Subsonic batch endpoints if available
2. **Caching**: Cache song ID mappings between runs
3. **Fuzzy matching**: Use fuzzy string matching for better song matching
4. **Progress bars**: Show progress during song matching
5. **Dry run mode**: Preview what would be synced without actually syncing
6. **Playlist metadata**: Sync playlist description, public/private status
7. **Multiple servers**: Support syncing to multiple Navidrome instances

## Troubleshooting

See README.md for detailed troubleshooting guide covering:
- Authentication failures
- Song matching issues
- Connection timeouts
- Empty playlists
- Network connectivity

## API Reference

### NavidromeClient

```python
client = NavidromeClient(
    base_url="http://localhost:4533",
    username="admin",
    password="password",
    client_id="vibe-dj",
    api_version="1.16.1"
)

# Search for a song
song_id = client.search_song(title="Song", artist="Artist", album="Album")

# Get all playlists
playlists = client.get_playlists()

# Find playlist by name
playlist = client.get_playlist_by_name("My Playlist")

# Create new playlist
playlist_id = client.create_playlist("New Playlist", ["song1", "song2"])

# Update playlist
client.update_playlist(playlist_id, song_ids_to_add=["song3"])

# Replace all songs in playlist
client.replace_playlist_songs(playlist_id, ["new1", "new2"])
```

## Dependencies

- `requests>=2.31.0`: HTTP client for Subsonic API calls
