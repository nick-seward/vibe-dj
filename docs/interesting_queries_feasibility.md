# Query Feasibility Analysis

This document analyzes the feasibility of implementing each query category from `interesting_queries.md` using the current vibe-dj feature extraction and search capabilities.

---

## Current System Capabilities

**Feature Vector** (50 dimensions):

| Index Range | Dimensions | Feature |
|-------------|------------|---------|
| 0–12 | 13 | MFCC (timbral texture) |
| 13–44 | 32 | Chroma (pitch class distribution, only 12 meaningful) |
| 45 | 1 | Tempo (BPM) |
| 46 | 1 | Loudness (RMS energy) |
| 47 | 1 | Spectral Centroid (brightness) |
| 48 | 1 | Danceability (onset strength derived) |
| 49 | 1 | Acousticness (derived metric) |

**Search Mechanism**: `SimilarityIndex.search(query_vector, k)` returns nearest neighbors by L2 distance.

**Current Query Flow**: Seed songs → average vector → perturb → FAISS search → filter → sample → sort by BPM.

---

## Query-by-Query Analysis

### 1. Mood-Based Queries ✅ Implementable

| Query | How to Execute |
|-------|----------------|
| **High-energy tracks** | Construct synthetic vector with high values at indices 45 (tempo ~140+), 46 (loudness ~0.1+), 48 (danceability ~0.5+). Set MFCC/chroma to zeros or library average. |
| **Chill/ambient music** | Low tempo (~60-80), low loudness (~0.01-0.02), low danceability (~0.1). High acousticness (~0.8+). |
| **Aggressive/intense** | High spectral centroid (index 47), high loudness, fast tempo. |

**Implementation Example**:
```python
def create_mood_query(tempo=120, loudness=0.05, centroid=2000, danceability=0.3, acousticness=0.5):
    # Use library-average MFCC/chroma or zeros
    mfcc = np.zeros(13, dtype=np.float32)
    chroma = np.zeros(32, dtype=np.float32)
    return np.concatenate([mfcc, chroma, [tempo, loudness, centroid, danceability, acousticness]])
```

**Limitation**: MFCC/chroma zeros will bias distance calculations. Better approach: compute library-wide mean for those dimensions.

---

### 2. Timbre Similarity ⚠️ Partially Implementable

| Query | Feasibility |
|-------|-------------|
| **Vocal texture matching** | ⚠️ MFCC captures *overall* timbre, not vocals specifically. Works if vocals dominate the mix. |
| **Instrumental similarity** | ⚠️ Same limitation—MFCC reflects combined timbre, not isolated instruments. |

**How to Execute**:
```python
# Use a seed song's MFCC values (indices 0-12) as the query
# Zero out or average other dimensions to focus on timbre
seed_features = db.get_features(seed_song_id)
query = seed_features.feature_vector.copy()
query[45:] = library_average[45:]  # Neutralize tempo/loudness/etc.
```

**Limitation**: No source separation—vocals and instruments are mixed in MFCC. For true vocal matching, you'd need Essentia's voice detection or Spleeter separation.

---

### 3. Harmonic/Melodic Queries ✅ Mostly Implementable

| Query | How to Execute |
|-------|----------------|
| **Key/chord progression similarity** | Use chroma values (indices 13-44, but only 13-24 are meaningful). Songs in the same key will have similar chroma profiles. |
| **Find songs in similar keys** | Extract chroma from a song in the target key, use as query with other dimensions neutralized. |
| **Melodic contour matching** | ❌ **Not possible**—chroma is pitch class distribution, not melodic sequence. Would need additional features. |

**Implementation**:
```python
# Focus on chroma similarity
query = library_average.copy()
query[13:25] = seed_features.feature_vector[13:25]  # Copy chroma from seed
# Search will find harmonically similar songs
```

---

### 4. Rhythm & Tempo Queries ✅ Implementable

| Query | How to Execute |
|-------|----------------|
| **BPM-constrained similarity** | FAISS search + post-filter by BPM range from database. |
| **Groove matching** | Weight tempo (index 45) and danceability (index 48) heavily in query. |
| **Workout playlists** | Generate playlist, then sort by BPM (already implemented in `sort_by_bpm`). |

**Implementation for BPM-constrained search**:
```python
# Search FAISS, then filter results
distances, song_ids = similarity_index.search(query, k=100)
filtered = [
    sid for sid in song_ids 
    if target_bpm - 5 <= db.get_features(sid).bpm <= target_bpm + 5
]
```

**Already Exists**: `PlaylistGenerator.sort_by_bpm()` sorts results by tempo.

---

### 5. Production Style Queries ✅ Implementable

| Query | How to Execute |
|-------|----------------|
| **Brightness matching** | Use spectral centroid (index 47) as primary dimension. |
| **Dynamic range** | ⚠️ Loudness (index 46) is RMS average, not dynamic range. Would need additional feature (loudness variance). |
| **Acoustic vs. electronic** | Use acousticness (index 49). Higher = more acoustic. |

**Implementation**:
```python
# Find bright songs
query = library_average.copy()
query[47] = 5000.0  # High spectral centroid = bright
query[49] = 0.2     # Low acousticness = electronic
```

---

### 6. Advanced Composite Queries ✅ Implementable

| Query | How to Execute |
|-------|----------------|
| **Genre-agnostic similarity** | ✅ Already the default—FAISS ignores metadata, uses only acoustic features. |
| **Transition-friendly tracks** | Search similar + filter for BPM within ±5-10 of seed. |
| **Contrast discovery** | Invert the feature vector: `inverted = 2 * library_mean - seed_vector` |
| **Micro-genre clustering** | Run k-means on all feature vectors, then explore clusters. |

**Contrast Discovery Implementation**:
```python
# Find acoustically opposite songs
library_mean = np.mean(all_vectors, axis=0)
seed_vector = db.get_features(seed_id).feature_vector
inverted = 2 * library_mean - seed_vector  # Reflect across mean
distances, opposite_ids = similarity_index.search(inverted, k=20)
```

**Clustering Implementation**:
```python
from sklearn.cluster import KMeans

all_vectors = np.array([f.feature_vector for _, f in db.get_all_songs_with_features()])
kmeans = KMeans(n_clusters=20).fit(all_vectors)
# kmeans.labels_ gives cluster assignment for each song
```

---

### 7. Creative Discovery ✅ Implementable

| Query | How to Execute |
|-------|----------------|
| **"Sounds like X but different"** | Search with seed vector, exclude seed + top N neighbors from results. |
| **Cross-genre bridges** | Average vectors from two different genre seeds, search for songs near that midpoint. |
| **Evolution tracking** | Query each album chronologically, plot feature drift over time. |

**"Sounds Like X But Different"**:
```python
# Already supported via exclude_ids parameter
similar = generator.find_similar_songs(
    query_vector=seed_vector,
    count=20,
    exclude_ids={seed_id, *top_5_neighbor_ids}  # Exclude seed and closest matches
)
```

**Cross-Genre Bridge**:
```python
jazz_vector = db.get_features(jazz_song_id).feature_vector
electronic_vector = db.get_features(electronic_song_id).feature_vector
bridge_query = (jazz_vector + electronic_vector) / 2
# Songs near this midpoint bridge both genres acoustically
```

---

### 8. Practical DJ/Playlist Use Cases ✅ Mostly Implemented

| Query | Status |
|-------|--------|
| **Seamless transitions** | ✅ `sort_by_bpm()` + similarity search already does this. |
| **Energy curve building** | ⚠️ Requires manual sequencing by loudness/danceability progression. |
| **Surprise elements** | ✅ Use `candidate_multiplier` + random sampling (already implemented). |
| **Set building** | ✅ Core functionality of `PlaylistGenerator.generate()`. |

**Energy Curve Implementation** (not yet built):
```python
def build_energy_curve(songs, target_curve="ascending"):
    # Sort by loudness + danceability composite
    def energy(song):
        f = db.get_features(song.id)
        return f.feature_vector[46] + f.feature_vector[48]  # loudness + danceability
    
    sorted_songs = sorted(songs, key=energy, reverse=(target_curve == "descending"))
    return sorted_songs
```

---

### 9. Analysis & Exploration ✅ Implementable

| Query | How to Execute |
|-------|----------------|
| **Outlier detection** | Compute distance from each song to library centroid. Highest distances = outliers. |
| **Cluster visualization** | K-means + dimensionality reduction (PCA/t-SNE) for 2D plot. |
| **Feature importance** | Perturb individual dimensions, observe search result changes. |

**Outlier Detection**:
```python
all_vectors = np.array([f.feature_vector for _, f in db.get_all_songs_with_features()])
centroid = np.mean(all_vectors, axis=0)
distances = np.linalg.norm(all_vectors - centroid, axis=1)
outlier_indices = np.argsort(distances)[-20:]  # Top 20 outliers
```

**Cluster Visualization**:
```python
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

pca = PCA(n_components=2)
reduced = pca.fit_transform(all_vectors)
kmeans = KMeans(n_clusters=10).fit(all_vectors)

plt.scatter(reduced[:, 0], reduced[:, 1], c=kmeans.labels_, cmap='tab10')
plt.title("Music Library Clusters")
```

---

## Summary Table

| Category | Implementable | Notes |
|----------|---------------|-------|
| 1. Mood-Based | ✅ Yes | Synthetic vectors with target values |
| 2. Timbre Similarity | ⚠️ Partial | MFCC captures overall timbre, not isolated vocals/instruments |
| 3. Harmonic/Melodic | ✅ Mostly | Chroma works for key/harmony; melodic contour not captured |
| 4. Rhythm & Tempo | ✅ Yes | BPM filtering + sort already exists |
| 5. Production Style | ✅ Yes | Centroid/acousticness available |
| 6. Advanced Composite | ✅ Yes | Vector math + clustering |
| 7. Creative Discovery | ✅ Yes | Exclusion, averaging, tracking |
| 8. DJ/Playlist | ✅ Mostly | Core functionality exists |
| 9. Analysis | ✅ Yes | Standard ML techniques |

---

## Key Limitations

The current features **do not capture**:

1. **Mood/Emotion** - No happy/sad/relaxed classification
2. **Vocal Presence** - Cannot distinguish vocal vs. instrumental tracks
3. **Specific Instruments** - Cannot identify guitar, piano, drums, etc.
4. **Melodic Contour** - Chroma captures pitch distribution, not melody shape
5. **Dynamic Range** - Only average loudness, not loudness variation

These limitations could be addressed by integrating **Essentia** pre-trained models as documented in `enhanced-audio-features.md`.

---

## Implementation Priority

For maximum impact with minimal effort:

1. **Compute library statistics** - Mean/std for each dimension to enable synthetic queries
2. **Add BPM filtering** - Post-filter FAISS results by BPM range
3. **Add energy sorting** - Sort by loudness + danceability composite
4. **Add clustering endpoint** - K-means for micro-genre discovery
5. **Add outlier detection** - Find unique songs in library

These require no changes to feature extraction—only new query/analysis functions.
