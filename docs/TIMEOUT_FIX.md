# Timeout/Deadlock Fix

**NOTE**: This document describes the initial timeout fix. A subsequent issue with ProcessPoolExecutor segfaults was discovered and fixed using ThreadPoolExecutor. See `THREADING_FIX.md` for the final solution.

## Problem

The indexer was deadlocking when processing audio files, getting stuck at 84% completion (31/37 files). The remaining 6 files caused the worker processes to hang indefinitely.

### Root Cause

The original implementation used `signal.alarm()` for timeout handling in the worker processes:

```python
def _worker_process_file(args):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    # ... process file ...
```

**Issue**: `signal.alarm()` only works reliably in the main thread on Unix systems. When used in multiprocessing worker processes spawned by `multiprocessing.Pool`, signals either:
- Don't work at all (signal gets ignored)
- Cause the worker to hang indefinitely
- Create race conditions with multiprocessing infrastructure

This is a well-known limitation of using signals with multiprocessing.

## Solution

Replaced `multiprocessing.Pool` with `concurrent.futures.ProcessPoolExecutor` and moved timeout handling to the orchestration level.

### Changes Made

#### 1. Updated `src/vibe_dj/core/indexer.py`

**Before:**
```python
from multiprocessing import Pool

def _worker_process_file(args):
    analyzer = AudioAnalyzer(config)
    features = analyzer.extract_features_with_timeout(file_path)  # Signal-based timeout
    return (file_path, features, features.bpm)

# In extract_features_phase:
pool = Pool(processes=self.config.parallel_workers)
results_iter = pool.imap_unordered(_worker_process_file, args_list)
for file_path, features, bpm in tqdm(results_iter, ...):
    # Process results
```

**After:**
```python
from concurrent.futures import ProcessPoolExecutor, TimeoutError, as_completed

def _worker_process_file(args):
    analyzer = AudioAnalyzer(config)
    features = analyzer.extract_features(file_path)  # No timeout in worker
    return (file_path, features, features.bpm)

# In extract_features_phase:
with ProcessPoolExecutor(max_workers=self.config.parallel_workers) as executor:
    future_to_file = {executor.submit(_worker_process_file, args): args[0] 
                      for args in args_list}
    
    for future in as_completed(future_to_file):
        file_path = future_to_file[future]
        try:
            result = future.result(timeout=timeout_seconds)  # Timeout at orchestration level
            # Process result
        except TimeoutError:
            logger.warning(f"Timeout ({timeout_seconds}s) processing: {file_path}")
```

#### 2. Updated `src/vibe_dj/core/analyzer.py`

- Removed `import signal`
- Removed `extract_features_with_timeout()` method (no longer needed)
- Workers now only call `extract_features()` directly

### Benefits

1. **Reliable Timeout Handling**: `future.result(timeout=...)` works correctly with worker processes
2. **Better Error Handling**: Each file's timeout is handled independently
3. **Graceful Degradation**: Timeout files are logged and skipped, processing continues
4. **Cleaner Code**: Timeout logic centralized at orchestration level
5. **Better Cancellation**: `executor.shutdown(wait=False, cancel_futures=True)` on Ctrl+C

### How It Works

1. **Submission**: All files are submitted to the executor as futures
2. **Completion Tracking**: `as_completed()` yields futures as they finish
3. **Timeout Enforcement**: `future.result(timeout=30)` waits max 30 seconds per file
4. **Timeout Handling**: If timeout occurs, `TimeoutError` is caught, logged, and processing continues
5. **Progress Updates**: Progress bar updates regardless of success/failure/timeout

### Testing

All 75 unit tests pass:
```bash
pytest tests/unit/ -v
# 75 passed, 3 warnings in 3.10s
```

### Configuration

Timeout is controlled by `processing_timeout` in config (default: 30 seconds):

```json
{
  "processing_timeout": 30
}
```

## Expected Behavior After Fix

When running `vibe-dj index ~/tempmusic`:

1. Files that process successfully: Added to database
2. Files that timeout (>30s): Logged as warning, skipped, processing continues
3. Files that error: Logged as error, skipped, processing continues
4. Progress bar: Always reaches 100% (all files attempted)
5. Summary: Shows successful vs failed counts

Example output:
```
Librosa analysis: 100%|████████████████████| 37/37 [00:45<00:00, 1.22s/song]
2026-01-01 13:10:15.234 | WARNING  | ... - Timeout (30s) processing: /path/problematic.mp3
2026-01-01 13:10:15.456 | INFO     | ... - All librosa processing complete
Indexing Summary:
  Successfully processed: 31/37 songs
  Failed: 6
```

## Migration Notes

- No API changes for users
- No configuration changes required
- Existing databases and indexes compatible
- Default timeout remains 30 seconds
