# Technical Specification: UI-to-Vector Mapping

This document specifies how UI controls map to the 50-dimensional feature vector used by the FAISS similarity search.

---

## Overview

The visual query builder translates user-friendly controls (sliders, radar chart points) into a 50-dimensional numpy array that can be passed to `SimilarityIndex.search()`.

---

## Feature Vector Structure

| Index | Feature | UI Control | Raw Range | Normalized Range |
|-------|---------|------------|-----------|------------------|
| 0-12 | MFCC (13 coefficients) | Complexity slider | Varies | Use library stats |
| 13-24 | Chroma (12 pitch classes) | Harmonic Richness slider | 0.0 - 1.0 | Sum of energy |
| 25-44 | Chroma padding (zeros) | N/A | 0.0 | Always 0 |
| 45 | Tempo (BPM) | Tempo slider | 60 - 180 | Direct mapping |
| 46 | Loudness (RMS) | Energy slider (partial) | 0.0 - 0.2 | 0.0 - 1.0 |
| 47 | Spectral Centroid | Brightness slider | 500 - 8000 Hz | 0.0 - 1.0 |
| 48 | Danceability | Danceability slider | 0.0 - 1.0 | Direct mapping |
| 49 | Acousticness | Acoustic slider | 0.0 - 1.0 | Direct mapping |

---

## UI Controls to Feature Mapping

### 1. Tempo Slider

**UI Range**: 0.0 to 1.0 (Slow to Fast)
**Feature Index**: 45
**Mapping Formula**:

```python
def tempo_ui_to_feature(ui_value: float) -> float:
    """Convert tempo slider (0-1) to BPM (60-180)."""
    MIN_BPM = 60
    MAX_BPM = 180
    return MIN_BPM + ui_value * (MAX_BPM - MIN_BPM)

def tempo_feature_to_ui(bpm: float) -> float:
    """Convert BPM to tempo slider value."""
    MIN_BPM = 60
    MAX_BPM = 180
    return (bpm - MIN_BPM) / (MAX_BPM - MIN_BPM)
```

**Example**:
- UI = 0.0 → 60 BPM (very slow)
- UI = 0.5 → 120 BPM (moderate)
- UI = 1.0 → 180 BPM (very fast)

---

### 2. Energy Slider

**UI Range**: 0.0 to 1.0 (Calm to Intense)
**Feature Indices**: 46 (Loudness) + 48 (Danceability) combined
**Mapping Formula**:

```python
def energy_ui_to_features(ui_value: float) -> tuple[float, float]:
    """Convert energy slider to loudness and danceability contribution."""
    # Loudness: 0.0 - 0.15 typical range
    loudness = ui_value * 0.15
    
    # Danceability gets a boost from energy (but has its own slider too)
    danceability_boost = ui_value * 0.3
    
    return loudness, danceability_boost

def energy_feature_to_ui(loudness: float, danceability: float) -> float:
    """Estimate energy from loudness and danceability."""
    # Weighted combination
    loudness_normalized = min(loudness / 0.15, 1.0)
    danceability_normalized = min(danceability / 0.8, 1.0)
    return 0.6 * loudness_normalized + 0.4 * danceability_normalized
```

**Note**: Energy is a composite control affecting multiple features.

---

### 3. Brightness Slider

**UI Range**: 0.0 to 1.0 (Warm/Dark to Bright/Sharp)
**Feature Index**: 47 (Spectral Centroid)
**Mapping Formula**:

```python
def brightness_ui_to_feature(ui_value: float) -> float:
    """Convert brightness slider to spectral centroid (Hz)."""
    MIN_CENTROID = 500    # Very warm/dark
    MAX_CENTROID = 8000   # Very bright/sharp
    return MIN_CENTROID + ui_value * (MAX_CENTROID - MIN_CENTROID)

def brightness_feature_to_ui(centroid: float) -> float:
    """Convert spectral centroid to brightness slider value."""
    MIN_CENTROID = 500
    MAX_CENTROID = 8000
    return max(0, min(1, (centroid - MIN_CENTROID) / (MAX_CENTROID - MIN_CENTROID)))
```

**Example**:
- UI = 0.0 → 500 Hz (warm, bass-heavy)
- UI = 0.5 → 4250 Hz (balanced)
- UI = 1.0 → 8000 Hz (bright, treble-heavy)

---

### 4. Acoustic Slider

**UI Range**: 0.0 to 1.0 (Electronic to Organic)
**Feature Index**: 49 (Acousticness)
**Mapping Formula**:

```python
def acoustic_ui_to_feature(ui_value: float) -> float:
    """Convert acoustic slider to acousticness value."""
    # Direct 1:1 mapping
    return ui_value

def acoustic_feature_to_ui(acousticness: float) -> float:
    """Convert acousticness to slider value."""
    return max(0, min(1, acousticness))
```

**Example**:
- UI = 0.0 → 0.0 (fully electronic/synthetic)
- UI = 0.5 → 0.5 (mixed)
- UI = 1.0 → 1.0 (fully acoustic/organic)

---

### 5. Danceability Slider

**UI Range**: 0.0 to 1.0 (Ambient to Groovy)
**Feature Index**: 48 (Danceability)
**Mapping Formula**:

```python
def danceability_ui_to_feature(ui_value: float) -> float:
    """Convert danceability slider to feature value."""
    MAX_DANCEABILITY = 0.8  # Typical max in dataset
    return ui_value * MAX_DANCEABILITY

def danceability_feature_to_ui(danceability: float) -> float:
    """Convert danceability feature to slider value."""
    MAX_DANCEABILITY = 0.8
    return min(1.0, danceability / MAX_DANCEABILITY)
```

---

### 6. Complexity Slider (MFCC-based)

**UI Range**: 0.0 to 1.0 (Simple to Complex)
**Feature Indices**: 0-12 (MFCC coefficients)
**Mapping Strategy**: Use library statistics

```python
def complexity_ui_to_features(
    ui_value: float, 
    library_stats: dict
) -> np.ndarray:
    """
    Convert complexity slider to MFCC values.
    
    Complexity is approximated by MFCC variance - more complex
    timbres have higher variance in MFCC coefficients.
    """
    mfcc_mean = library_stats['mfcc_mean']      # Shape: (13,)
    mfcc_std = library_stats['mfcc_std']        # Shape: (13,)
    
    # Low complexity = near mean, high complexity = further from mean
    # Scale from -1 std to +1 std based on ui_value
    scale = (ui_value - 0.5) * 2  # Maps 0-1 to -1 to +1
    
    return mfcc_mean + scale * mfcc_std

def complexity_feature_to_ui(
    mfcc: np.ndarray, 
    library_stats: dict
) -> float:
    """Estimate complexity from MFCC values."""
    mfcc_mean = library_stats['mfcc_mean']
    mfcc_std = library_stats['mfcc_std']
    
    # Calculate how far from mean (in std units)
    deviation = np.abs(mfcc - mfcc_mean) / (mfcc_std + 1e-6)
    avg_deviation = np.mean(deviation)
    
    # Normalize to 0-1 range (assuming max ~2 std deviations)
    return min(1.0, avg_deviation / 2.0)
```

---

### 7. Harmonic Richness Slider (Chroma-based)

**UI Range**: 0.0 to 1.0 (Sparse to Rich)
**Feature Indices**: 13-24 (Chroma, 12 pitch classes)
**Mapping Strategy**: Scale chroma energy

```python
def harmonic_ui_to_features(
    ui_value: float, 
    library_stats: dict
) -> np.ndarray:
    """
    Convert harmonic richness slider to chroma values.
    
    Low richness = few pitch classes active (sparse harmony)
    High richness = many pitch classes active (rich harmony)
    """
    chroma_mean = library_stats['chroma_mean']  # Shape: (12,)
    
    # Scale the chroma energy based on UI value
    # Low UI = suppress to near zero, High UI = amplify
    scale = 0.2 + ui_value * 1.6  # Range: 0.2 to 1.8
    
    return chroma_mean * scale

def harmonic_feature_to_ui(chroma: np.ndarray) -> float:
    """Estimate harmonic richness from chroma values."""
    # Sum of all chroma energy indicates harmonic richness
    total_energy = np.sum(chroma[:12])  # Only first 12 are meaningful
    
    # Normalize (typical range 0-5)
    return min(1.0, total_energy / 5.0)
```

---

## Complete Vector Builder

```python
import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class UIQueryParams:
    """Parameters from the visual query builder UI."""
    tempo: float = 0.5           # 0-1: Slow to Fast
    energy: float = 0.5          # 0-1: Calm to Intense
    brightness: float = 0.5      # 0-1: Warm to Bright
    acoustic: float = 0.5        # 0-1: Electronic to Organic
    danceability: float = 0.5    # 0-1: Ambient to Groovy
    complexity: float = 0.5      # 0-1: Simple to Complex
    harmonic_richness: float = 0.5  # 0-1: Sparse to Rich
    
    # Importance weights (0 = ignore, 1 = strict)
    tempo_importance: float = 0.5
    energy_importance: float = 0.5
    brightness_importance: float = 0.5
    acoustic_importance: float = 0.5
    danceability_importance: float = 0.5
    complexity_importance: float = 0.5
    harmonic_importance: float = 0.5


@dataclass
class LibraryStats:
    """Pre-computed statistics from the music library."""
    mean: np.ndarray          # Shape: (50,) - mean of all vectors
    std: np.ndarray           # Shape: (50,) - std of all vectors
    mfcc_mean: np.ndarray     # Shape: (13,)
    mfcc_std: np.ndarray      # Shape: (13,)
    chroma_mean: np.ndarray   # Shape: (12,)
    chroma_std: np.ndarray    # Shape: (12,)
    
    @classmethod
    def compute_from_database(cls, database) -> 'LibraryStats':
        """Compute library statistics from all songs."""
        songs_with_features = database.get_all_songs_with_features()
        vectors = np.array([f.feature_vector for _, f in songs_with_features])
        
        return cls(
            mean=np.mean(vectors, axis=0),
            std=np.std(vectors, axis=0),
            mfcc_mean=np.mean(vectors[:, 0:13], axis=0),
            mfcc_std=np.std(vectors[:, 0:13], axis=0),
            chroma_mean=np.mean(vectors[:, 13:25], axis=0),
            chroma_std=np.std(vectors[:, 13:25], axis=0),
        )


class QueryVectorBuilder:
    """Builds FAISS query vectors from UI parameters."""
    
    def __init__(self, library_stats: LibraryStats):
        self.stats = library_stats
    
    def build_query_vector(self, params: UIQueryParams) -> np.ndarray:
        """
        Convert UI parameters to a 50-dimensional query vector.
        
        :param params: UI slider values and importance weights
        :return: 50-dimensional numpy array for FAISS search
        """
        # Start with library mean as baseline
        query = self.stats.mean.copy()
        
        # Apply MFCC (complexity)
        if params.complexity_importance > 0:
            mfcc_values = self._complexity_to_mfcc(params.complexity)
            query[0:13] = self._blend_with_importance(
                query[0:13], mfcc_values, params.complexity_importance
            )
        
        # Apply Chroma (harmonic richness)
        if params.harmonic_importance > 0:
            chroma_values = self._harmonic_to_chroma(params.harmonic_richness)
            query[13:25] = self._blend_with_importance(
                query[13:25], chroma_values, params.harmonic_importance
            )
        
        # Chroma padding stays at zero
        query[25:45] = 0.0
        
        # Apply Tempo
        if params.tempo_importance > 0:
            tempo_value = 60 + params.tempo * 120  # 60-180 BPM
            query[45] = self._blend_with_importance(
                query[45], tempo_value, params.tempo_importance
            )
        
        # Apply Energy (affects loudness)
        if params.energy_importance > 0:
            loudness_value = params.energy * 0.15
            query[46] = self._blend_with_importance(
                query[46], loudness_value, params.energy_importance
            )
        
        # Apply Brightness (spectral centroid)
        if params.brightness_importance > 0:
            centroid_value = 500 + params.brightness * 7500  # 500-8000 Hz
            query[47] = self._blend_with_importance(
                query[47], centroid_value, params.brightness_importance
            )
        
        # Apply Danceability
        if params.danceability_importance > 0:
            dance_value = params.danceability * 0.8
            # Also factor in energy contribution
            dance_value += params.energy * 0.2
            dance_value = min(0.8, dance_value)
            query[48] = self._blend_with_importance(
                query[48], dance_value, params.danceability_importance
            )
        
        # Apply Acousticness
        if params.acoustic_importance > 0:
            query[49] = self._blend_with_importance(
                query[49], params.acoustic, params.acoustic_importance
            )
        
        return query.astype(np.float32)
    
    def _blend_with_importance(
        self, 
        baseline: float | np.ndarray, 
        target: float | np.ndarray, 
        importance: float
    ) -> float | np.ndarray:
        """
        Blend baseline (library mean) with target value based on importance.
        
        importance = 0: Return baseline (ignore this dimension)
        importance = 1: Return target (strict matching)
        importance = 0.5: Return midpoint
        """
        return baseline * (1 - importance) + target * importance
    
    def _complexity_to_mfcc(self, complexity: float) -> np.ndarray:
        """Convert complexity slider to MFCC values."""
        scale = (complexity - 0.5) * 2  # -1 to +1
        return self.stats.mfcc_mean + scale * self.stats.mfcc_std
    
    def _harmonic_to_chroma(self, richness: float) -> np.ndarray:
        """Convert harmonic richness to chroma values."""
        scale = 0.2 + richness * 1.6  # 0.2 to 1.8
        return self.stats.chroma_mean * scale
```

---

## Preset Definitions

```python
PRESETS = {
    "party": UIQueryParams(
        tempo=0.8,              # Fast (144 BPM)
        energy=0.9,             # High energy
        brightness=0.7,         # Bright
        acoustic=0.2,           # Electronic
        danceability=0.9,       # Very danceable
        complexity=0.5,         # Medium complexity
        harmonic_richness=0.6,  # Moderately rich
        # All importance high for party
        tempo_importance=0.8,
        energy_importance=0.9,
        brightness_importance=0.6,
        acoustic_importance=0.7,
        danceability_importance=0.9,
        complexity_importance=0.3,
        harmonic_importance=0.3,
    ),
    
    "chill": UIQueryParams(
        tempo=0.25,             # Slow (90 BPM)
        energy=0.2,             # Calm
        brightness=0.3,         # Warm
        acoustic=0.7,           # Organic
        danceability=0.2,       # Low danceability
        complexity=0.4,         # Simple-ish
        harmonic_richness=0.5,  # Medium harmony
        # Moderate importance
        tempo_importance=0.6,
        energy_importance=0.8,
        brightness_importance=0.5,
        acoustic_importance=0.7,
        danceability_importance=0.6,
        complexity_importance=0.3,
        harmonic_importance=0.3,
    ),
    
    "workout": UIQueryParams(
        tempo=0.85,             # Fast (162 BPM)
        energy=0.95,            # Very high energy
        brightness=0.6,         # Moderately bright
        acoustic=0.3,           # More electronic
        danceability=0.8,       # High danceability
        complexity=0.4,         # Not too complex
        harmonic_richness=0.4,  # Simple harmony
        # High importance on tempo and energy
        tempo_importance=0.9,
        energy_importance=0.95,
        brightness_importance=0.4,
        acoustic_importance=0.5,
        danceability_importance=0.7,
        complexity_importance=0.2,
        harmonic_importance=0.2,
    ),
    
    "acoustic": UIQueryParams(
        tempo=0.4,              # Moderate (108 BPM)
        energy=0.4,             # Medium-low energy
        brightness=0.35,        # Warm
        acoustic=0.95,          # Very acoustic
        danceability=0.3,       # Low danceability
        complexity=0.5,         # Medium complexity
        harmonic_richness=0.6,  # Rich harmony
        # High importance on acoustic
        tempo_importance=0.4,
        energy_importance=0.5,
        brightness_importance=0.6,
        acoustic_importance=0.95,
        danceability_importance=0.4,
        complexity_importance=0.3,
        harmonic_importance=0.5,
    ),
    
    "electronic": UIQueryParams(
        tempo=0.7,              # Fast-ish (144 BPM)
        energy=0.7,             # High energy
        brightness=0.8,         # Very bright
        acoustic=0.05,          # Very electronic
        danceability=0.75,      # Danceable
        complexity=0.6,         # Moderately complex
        harmonic_richness=0.4,  # Simpler harmony
        # High importance on acoustic (inverted) and brightness
        tempo_importance=0.5,
        energy_importance=0.6,
        brightness_importance=0.7,
        acoustic_importance=0.9,
        danceability_importance=0.6,
        complexity_importance=0.4,
        harmonic_importance=0.3,
    ),
    
    "jazz": UIQueryParams(
        tempo=0.45,             # Moderate (114 BPM)
        energy=0.4,             # Medium energy
        brightness=0.5,         # Balanced
        acoustic=0.8,           # Mostly acoustic
        danceability=0.35,      # Some swing
        complexity=0.85,        # High complexity
        harmonic_richness=0.9,  # Very rich harmony
        # High importance on complexity and harmony
        tempo_importance=0.4,
        energy_importance=0.4,
        brightness_importance=0.3,
        acoustic_importance=0.7,
        danceability_importance=0.4,
        complexity_importance=0.85,
        harmonic_importance=0.9,
    ),
}
```

---

## Blend Mode Implementation

```python
def blend_song_vectors(
    vector_a: np.ndarray,
    vector_b: np.ndarray,
    blend_ratio: float  # 0.0 = 100% A, 1.0 = 100% B
) -> np.ndarray:
    """
    Create a blended query vector from two seed songs.
    
    :param vector_a: Feature vector of song A
    :param vector_b: Feature vector of song B
    :param blend_ratio: How much of B to include (0-1)
    :return: Blended feature vector
    """
    return (1 - blend_ratio) * vector_a + blend_ratio * vector_b
```

---

## API Endpoint Specification

### POST /api/query/visual

Build and execute a visual query.

**Request Body**:
```json
{
  "params": {
    "tempo": 0.7,
    "energy": 0.8,
    "brightness": 0.6,
    "acoustic": 0.3,
    "danceability": 0.75,
    "complexity": 0.5,
    "harmonic_richness": 0.5,
    "tempo_importance": 0.8,
    "energy_importance": 0.9,
    "brightness_importance": 0.5,
    "acoustic_importance": 0.6,
    "danceability_importance": 0.8,
    "complexity_importance": 0.3,
    "harmonic_importance": 0.3
  },
  "limit": 20
}
```

**Response**:
```json
{
  "results": [
    {
      "id": 123,
      "title": "Song Title",
      "artist": "Artist Name",
      "album": "Album Name",
      "match_score": 0.92,
      "features": {
        "tempo": 142,
        "energy": 0.78,
        "brightness": 0.65,
        "acoustic": 0.28,
        "danceability": 0.72
      }
    }
  ],
  "query_vector_preview": {
    "tempo": 144,
    "loudness": 0.12,
    "centroid": 5500,
    "danceability": 0.6,
    "acousticness": 0.3
  }
}
```

### POST /api/query/preset

Apply a preset and execute query.

**Request Body**:
```json
{
  "preset": "party",
  "limit": 20
}
```

### POST /api/query/blend

Blend two songs and execute query.

**Request Body**:
```json
{
  "song_a_id": 123,
  "song_b_id": 456,
  "blend_ratio": 0.65,
  "limit": 20
}
```

---

## Library Statistics Caching

Statistics should be computed once and cached:

```python
class LibraryStatsCache:
    """Cache for library statistics with invalidation."""
    
    def __init__(self, database, cache_path: str = "library_stats.json"):
        self.database = database
        self.cache_path = cache_path
        self._stats: Optional[LibraryStats] = None
        self._song_count: int = 0
    
    def get_stats(self) -> LibraryStats:
        """Get cached stats, recomputing if library changed."""
        current_count = self.database.count_songs()
        
        if self._stats is None or current_count != self._song_count:
            self._stats = LibraryStats.compute_from_database(self.database)
            self._song_count = current_count
            self._save_cache()
        
        return self._stats
    
    def _save_cache(self):
        """Persist stats to disk."""
        # Implementation: serialize numpy arrays to JSON
        pass
    
    def _load_cache(self) -> Optional[LibraryStats]:
        """Load stats from disk if available."""
        # Implementation: deserialize from JSON
        pass
```

---

## Match Score Calculation

Convert FAISS L2 distance to a 0-100% match score:

```python
def distance_to_match_score(distance: float, max_distance: float = 1000.0) -> float:
    """
    Convert L2 distance to percentage match score.
    
    :param distance: L2 distance from FAISS
    :param max_distance: Distance considered 0% match
    :return: Match score 0.0 to 1.0
    """
    # Inverse relationship: lower distance = higher match
    normalized = min(distance / max_distance, 1.0)
    return 1.0 - normalized

def distances_to_scores(distances: np.ndarray) -> np.ndarray:
    """Convert array of distances to match scores."""
    # Use the max distance in results as reference
    max_dist = max(distances.max(), 1.0)
    return 1.0 - (distances / max_dist)
```

---

## Radar Chart Coordinate Mapping

For rendering the radar chart, convert feature values to polar coordinates:

```python
import math

def features_to_radar_points(
    params: UIQueryParams,
    num_axes: int = 7,
    radius: float = 100.0
) -> list[tuple[float, float]]:
    """
    Convert UI parameters to radar chart (x, y) coordinates.
    
    :param params: Current UI parameter values
    :param num_axes: Number of axes on radar chart
    :param radius: Maximum radius in pixels
    :return: List of (x, y) coordinates for each axis point
    """
    values = [
        params.tempo,
        params.energy,
        params.brightness,
        params.acoustic,
        params.danceability,
        params.complexity,
        params.harmonic_richness,
    ]
    
    points = []
    angle_step = 2 * math.pi / num_axes
    
    for i, value in enumerate(values):
        angle = i * angle_step - math.pi / 2  # Start from top
        r = value * radius
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        points.append((x, y))
    
    return points
```
