# Migration Guide: Seed Song Format Update

## Overview

This guide covers the migration from title-only seed songs to the new format that requires **title, artist, and album** for exact matching.

## What Changed

### Old Format (No Longer Supported)
```json
{
  "seeds": ["Song Title 1", "Song Title 2"]
}
```

### New Format (Required)
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

## Why This Change?

The old format used fuzzy title matching, which caused ambiguity when multiple songs shared the same title. The new format uses exact matching on all three fields (title, artist, album) to ensure you get the exact song you intended.

## Migration Steps

### Step 1: Update Your Database Schema

The database now includes an `album` field. To populate it for existing songs, use the migration script:

```bash
# Run the migration script to populate album field
python scripts/migrate_add_album.py

# Or with a custom config
python scripts/migrate_add_album.py --config /path/to/config.json
```

**What happens:**
- Reads metadata from audio files and extracts album information
- Updates only the `album` field in the database
- Does NOT trigger librosa analysis (very fast)
- Skips songs that already have album populated
- Shows progress bar with statistics

**Alternative (if you want a full re-index):**
If you prefer to do a complete re-index from scratch:
```bash
# Backup your database first!
cp music.db music.db.backup

# Delete the database
rm music.db

# Re-run full indexing
vibe-dj index /path/to/music
```
Note: This will re-run librosa analysis on all files (slow).

### Step 2: Find Your Songs' Album Information

To find the exact title, artist, and album for your seed songs:

```bash
# List all songs in your database
sqlite3 music.db "SELECT title, artist, album FROM songs;"

# Search for a specific song
sqlite3 music.db "SELECT title, artist, album FROM songs WHERE title LIKE '%Song Name%';"

# Export to CSV for easier viewing
sqlite3 -header -csv music.db "SELECT title, artist, album FROM songs;" > songs.csv
```

### Step 3: Update Your seeds.json File

Replace your old seeds.json with the new format using the exact values from your database.

**Example:**

If your database shows:
```
title: Bohemian Rhapsody
artist: Queen
album: A Night at the Opera
```

Your seeds.json should be:
```json
{
  "seeds": [
    {
      "title": "Bohemian Rhapsody",
      "artist": "Queen",
      "album": "A Night at the Opera"
    }
  ]
}
```

### Step 4: Test Your Playlist Generation

```bash
vibe-dj playlist --seeds-json seeds.json --output test_playlist.m3u
```

If a seed song is not found, you'll see a warning message with the exact values you provided. Double-check they match your database exactly.

## Troubleshooting

### "No exact match found for seed"

**Cause:** The title, artist, or album doesn't match the database exactly.

**Solution:**
1. Query your database to see the exact values:
   ```bash
   sqlite3 music.db "SELECT title, artist, album FROM songs WHERE title LIKE '%YourSong%';"
   ```
2. Copy the exact values (case-sensitive, including spaces) into your seeds.json

### "Missing required fields in seed"

**Cause:** Your seeds.json is still using the old string format or missing a field.

**Solution:** Ensure each seed is a dictionary with all three fields: `title`, `artist`, and `album`.

### Album field shows "Unknown"

**Cause:** The audio file doesn't have album metadata in its tags.

**Solution:**
1. Use a tag editor (like MusicBrainz Picard, Mp3tag) to add album information to your files
2. Re-run the indexer after updating tags

## Docker Users

If using Docker, run the migration script by overriding the entrypoint:

```bash
# Run migration script (override entrypoint to use python)
docker run --rm \
  -v /path/to/music:/music:ro \
  -v $(pwd)/data:/data \
  --entrypoint python \
  vibe-dj /app/scripts/migrate_add_album.py

# Query database to verify
docker run --rm \
  -v $(pwd)/data:/data \
  --entrypoint sqlite3 \
  vibe-dj /data/music.db "SELECT title, artist, album FROM songs LIMIT 10;"
```

**Alternative - Full re-index:**
```bash
# Backup database
cp data/music.db data/music.db.backup

# Delete database and re-index
rm data/music.db
docker run --rm -v /path/to/music:/music:ro -v $(pwd)/data:/data vibe-dj index /music
```

## Benefits of the New Format

1. **No Ambiguity:** Multiple songs with the same title are distinguished by artist and album
2. **Exact Matching:** You always get the exact song you intended
3. **Better Control:** More precise playlist generation based on specific recordings
4. **Future-Proof:** Enables potential features like artist-based or album-based similarity

## Need Help?

If you encounter issues during migration, check:
1. Database has album field populated (run the re-index step)
2. Seeds.json uses the new dictionary format
3. Values in seeds.json match database exactly (case-sensitive)
