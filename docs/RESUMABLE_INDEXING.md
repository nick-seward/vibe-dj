# Resumable Indexing Implementation

## Overview

The vibe-dj CLI app now supports **resumable indexing**, allowing the indexing process to be interrupted and resumed without losing progress. This addresses the critical issue where crashes or user interruptions would force a complete restart of the indexing process.

## Key Changes

### 1. Incremental Database Persistence

**Before:** All metadata and features were collected in memory and only written to the database at the end of indexing.

**After:** Data is written to the database immediately after processing each file (or batch of files based on `batch_size` config).

### 2. Phase-Based Processing

#### Phase 1: Metadata Extraction
- Extracts file metadata (title, artist, genre, duration) using mutagen
- Writes each song to the database immediately (without features)
- Commits to database every `batch_size` songs (default: 10)
- Returns count of processed songs

#### Phase 2: Feature Extraction  
- Queries database for songs that have metadata but no features
- Extracts acoustic features using librosa (parallel processing)
- Updates database immediately when each song completes
- Commits to database every `batch_size` songs
- Returns count of processed songs

### 3. Progress Reporting

On restart, the indexer now displays:
```
============================================================
Existing Progress:
  Total songs in database: 150
  Songs with features: 120
  Songs without features: 30
============================================================
```

This helps users understand what work has already been completed.

### 4. Incremental FAISS Index Updates

**Before:** Always rebuilt the entire FAISS index from scratch.

**After:** 
- If no index exists → build from scratch
- If change is > 10% of existing index → rebuild from scratch
- If change is ≤ 10% of existing index → add new vectors incrementally
- Falls back to full rebuild on any errors

### 5. Transaction Isolation

Database commits are controlled by the `batch_size` configuration parameter:
- **Per-file commits** when `batch_size = 1` (maximum safety, slightly slower)
- **Batch commits** when `batch_size > 1` (faster, but could lose up to N files on crash)
- Default is `batch_size = 10` (good balance)

## New Database Methods

### `get_songs_without_features(file_paths: List[str] = None) -> List[Song]`
Returns songs that exist in the database but don't have features yet. Optionally filter by specific file paths.

### `get_indexing_stats() -> dict`
Returns statistics about indexing progress:
```python
{
    'total_songs': 150,
    'songs_with_features': 120,
    'songs_without_features': 30
}
```

## Usage Examples

### Normal Indexing
```bash
vibe-dj index /path/to/music
```

### Resume After Interruption
Simply run the same command again:
```bash
vibe-dj index /path/to/music
```

The indexer will:
1. Show existing progress
2. Skip files already processed
3. Continue extracting features for songs without them
4. Update the FAISS index incrementally

### Custom Batch Size
Create a config file to adjust commit frequency:
```json
{
  "batch_size": 5,
  "parallel_workers": 4
}
```

Then run:
```bash
vibe-dj index /path/to/music --config config.json
```

## Benefits

✅ **Resumable** - Restart picks up where it left off  
✅ **Memory efficient** - No large in-memory dictionaries  
✅ **Progress visible** - Database shows real-time progress  
✅ **Atomic writes** - Each song is committed, no partial corruption  
✅ **Backward compatible** - No breaking changes to CLI interface  
✅ **Faster restarts** - Incremental FAISS updates for small changes  

## Testing

### Unit Tests
- `tests/unit/core/test_database.py` - Tests for new database methods
- `tests/unit/core/test_indexer.py` - Tests for refactored indexing logic

### Integration Tests
- `tests/integration/test_resumable_indexing.py` - End-to-end resumability tests

Run all tests:
```bash
pytest tests/unit/ -v
pytest tests/integration/test_resumable_indexing.py -v
```

## Implementation Details

### File Structure Changes

**Modified Files:**
- `src/vibe_dj/core/database.py` - Added `get_songs_without_features()` and `get_indexing_stats()`
- `src/vibe_dj/core/indexer.py` - Refactored to use incremental persistence
- `tests/unit/core/test_database.py` - Added tests for new methods
- `tests/unit/core/test_indexer.py` - Updated tests for new implementation

**New Files:**
- `tests/integration/test_resumable_indexing.py` - Integration tests for resumability

### Backward Compatibility

All changes are backward compatible:
- Existing databases work without migration
- CLI interface unchanged
- Configuration parameters are additive only
- Existing FAISS indexes are reused when possible

## Performance Considerations

1. **Commit frequency**: Controlled by `batch_size` parameter
2. **Memory usage**: Significantly reduced (no in-memory accumulation)
3. **Disk I/O**: Slightly increased due to more frequent commits
4. **FAISS updates**: Incremental updates are faster for small changes

## Edge Cases Handled

1. **Crash during Phase 1** → Restart continues with unprocessed files
2. **Crash during Phase 2** → Songs have metadata, only missing features get processed
3. **File modified after Phase 1** → Detected via mtime check, re-processed
4. **Partial feature extraction** → Database query finds incomplete songs
5. **FAISS index corruption** → Falls back to full rebuild
6. **Keyboard interrupt** → Commits current progress before shutdown
