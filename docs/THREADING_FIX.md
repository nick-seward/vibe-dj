# Threading Implementation Fix

## Problem

The ProcessPoolExecutor implementation was causing segmentation faults in worker processes when processing audio files with librosa on macOS.

### Root Cause

**Segmentation Fault in Worker Processes**: When using `ProcessPoolExecutor` on macOS, worker processes were crashing with segfaults when attempting to use librosa for audio feature extraction.

**Why it happened**:
1. macOS uses the `spawn` multiprocessing start method by default
2. When processes are spawned, each worker imports modules in a fresh Python interpreter
3. Scientific libraries with C extensions (librosa, numpy, numba) can have initialization issues in spawned processes
4. This caused worker processes to crash with: "A process in the process pool was terminated abruptly while the future was running or pending"

**Evidence**:
- 100% failure rate: All 37 files failed to process
- Direct test of worker function resulted in segmentation fault (exit code 139)
- Librosa worked fine in main process but crashed in spawned workers

## Solution

Replaced `ProcessPoolExecutor` with `ThreadPoolExecutor` and implemented shared `AudioAnalyzer` pattern.

### Why Threading Works

**GIL is Not a Bottleneck for This Workload**:

1. **I/O Operations Release GIL**: Audio file loading releases the Global Interpreter Lock
2. **C Extension Calls Release GIL**: librosa, numpy, and numba operations release GIL during computation
3. **Minimal Pure Python**: Most processing time is spent in I/O and C extensions, not pure Python code

**Expected Performance**: Near-parallel performance since workers spend most time with GIL released.

### Changes Made

#### 1. Updated `src/vibe_dj/core/indexer.py`

**Import Change**:
```python
# Before
from concurrent.futures import ProcessPoolExecutor, TimeoutError, as_completed

# After
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
```

**Worker Function Change**:
```python
# Before
def _worker_process_file(args: Tuple[str, Config]) -> Tuple[str, Optional[Features], Optional[float]]:
    file_path, config = args
    analyzer = AudioAnalyzer(config)  # Creates new analyzer per file
    features = analyzer.extract_features(file_path)
    return (file_path, features, features.bpm if features else None)

# After
def _worker_thread_file(args: Tuple[str, AudioAnalyzer]) -> Tuple[str, Optional[Features], Optional[float]]:
    file_path, analyzer = args  # Shared analyzer instance
    features = analyzer.extract_features(file_path)
    return (file_path, features, features.bpm if features else None)
```

**Executor Change**:
```python
# Before
with ProcessPoolExecutor(max_workers=self.config.parallel_workers) as executor:
    args_list = [(f, self.config) for f in files]
    future_to_file = {executor.submit(_worker_process_file, args): args[0] for args in args_list}

# After
with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
    args_list = [(f, self.analyzer) for f in files]  # Pass shared analyzer
    future_to_file = {executor.submit(_worker_thread_file, args): args[0] for args in args_list}
```

#### 2. Updated `src/vibe_dj/models/config.py`

**Adaptive Worker Count**:
```python
# Before
parallel_workers: int = 4

# After
parallel_workers: int = field(default_factory=lambda: os.cpu_count() or 4)
```

Now automatically adapts to the number of CPU cores available, defaulting to 4 if `cpu_count()` returns None.

#### 3. Updated `tests/unit/models/test_config.py`

Updated test to expect adaptive worker count:
```python
# Before
self.assertEqual(config.parallel_workers, 4)

# After
self.assertEqual(config.parallel_workers, os.cpu_count() or 4)
```

### Thread Safety Analysis

All operations are thread-safe because:

| Component | Thread-Safe? | Reasoning |
|-----------|--------------|-----------|
| `AudioAnalyzer.extract_features()` | ✅ Yes | Only reads files, no shared state mutation |
| `AudioAnalyzer.extract_metadata()` | ✅ Yes | Only reads files, no shared state mutation |
| `AudioAnalyzer.get_duration()` | ✅ Yes | Only reads files, no shared state mutation |
| librosa operations | ✅ Yes | Pure computation, no global state |
| numpy operations | ✅ Yes | Thread-safe for independent arrays |
| MusicBrainz API calls | ✅ Yes | Sequential per thread, has rate limiting |

**Key Point**: Each thread processes different files with no shared mutable state, making the implementation inherently thread-safe.

### Benefits

1. **No Segmentation Faults**: Threads share the same memory space, avoiding spawn-related issues
2. **Shared AudioAnalyzer**: Reduces object creation overhead
3. **Adaptive Worker Count**: Automatically uses optimal number of workers based on CPU cores
4. **Better Performance**: No pickling overhead, faster startup
5. **Same Timeout Handling**: `future.result(timeout=...)` works identically for threads
6. **Cleaner Code**: Simpler worker function signature

### Testing Results

**Unit Tests**: All 75 tests pass ✅
```bash
pytest tests/unit/ -v
# 75 passed, 3 warnings in 2.99s
```

**Integration Tests**: 10 consecutive runs, 100% success rate ✅
```
Run 10/10:
  Successfully processed: 37/37 songs
  Failed: 0
  No segmentation faults
  No process termination errors
```

**Performance**: ~1.3 songs/second average processing speed with 8 workers on test machine.

### Configuration

Worker count is now adaptive but can still be overridden:

**Default (Adaptive)**:
```python
config = Config()  # Uses os.cpu_count() or 4
```

**Custom**:
```python
config = Config(parallel_workers=4)  # Override to specific value
```

**From File**:
```json
{
  "parallel_workers": 4,
  "processing_timeout": 30
}
```

### Migration Notes

- **No Breaking Changes**: Existing configurations still work
- **Better Defaults**: Automatically adapts to available CPU cores
- **Same API**: All timeout and error handling remains unchanged
- **Performance**: Equal or better than ProcessPoolExecutor (if it worked)

### Comparison: Before vs After

| Aspect | ProcessPoolExecutor | ThreadPoolExecutor |
|--------|---------------------|-------------------|
| Success Rate | 0% (segfaults) | 100% ✅ |
| Worker Isolation | Separate processes | Shared memory |
| Startup Overhead | High (spawn + pickle) | Low (thread creation) |
| GIL Impact | None | Minimal (I/O + C extensions) |
| Timeout Handling | ✅ Works | ✅ Works |
| Memory Usage | Higher | Lower |
| macOS Compatibility | ❌ Segfaults | ✅ Works |

## Conclusion

The ThreadPoolExecutor implementation solves the segmentation fault issue while maintaining performance and improving code simplicity. The GIL is not a bottleneck for this I/O and C-extension heavy workload, making threading an ideal solution.

**Result**: Reliable, performant audio indexing on macOS with no segmentation faults.
