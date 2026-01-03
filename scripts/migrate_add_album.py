#!/usr/bin/env python3
"""
Migration script to populate album field for existing songs.
This reads metadata from audio files and updates the database without
triggering a full re-index or librosa analysis.
"""

import sys
import os
from pathlib import Path
from tqdm import tqdm

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vibe_dj.models import Config
from vibe_dj.core.database import MusicDatabase
from vibe_dj.core.analyzer import AudioAnalyzer


def migrate_album_field(config: Config):
    """Populate album field for all songs in the database."""
    
    db = MusicDatabase(config)
    db.connect()
    
    # Ensure database schema is up to date (adds album column if missing)
    print("Ensuring database schema is up to date...")
    db.init_db()
    
    analyzer = AudioAnalyzer(config)
    
    # Get all songs
    cursor = db.connection.cursor()
    cursor.execute("SELECT id, file_path, album FROM songs")
    songs = cursor.fetchall()
    
    print(f"Found {len(songs)} songs in database")
    
    updated = 0
    skipped = 0
    errors = 0
    
    for row in tqdm(songs, desc="Updating album metadata", unit="song"):
        song_id = row["id"]
        file_path = row["file_path"]
        current_album = row["album"]
        
        # Skip if album already populated
        if current_album and current_album != "Unknown":
            skipped += 1
            continue
        
        # Skip if file doesn't exist
        if not os.path.exists(file_path):
            errors += 1
            continue
        
        try:
            # Extract metadata
            title, artist, album, genre = analyzer.extract_metadata(file_path)
            
            # Update only the album field
            cursor.execute(
                "UPDATE songs SET album = ? WHERE id = ?",
                (album, song_id)
            )
            updated += 1
            
            # Commit in batches
            if updated % 100 == 0:
                db.commit()
                
        except Exception as e:
            print(f"\nError processing {file_path}: {e}")
            errors += 1
    
    # Final commit
    db.commit()
    db.close()
    
    print(f"\nMigration complete:")
    print(f"  Updated: {updated}")
    print(f"  Skipped (already had album): {skipped}")
    print(f"  Errors: {errors}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate database to add album field")
    parser.add_argument("--config", type=str, help="Path to config file")
    args = parser.parse_args()
    
    if args.config:
        config = Config.from_file(args.config)
    else:
        config = Config()
    
    print(f"Using database: {config.database_path}")
    migrate_album_field(config)
