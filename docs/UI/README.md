# Visual Query Builder UI Exploration

This directory contains design documentation for a visual query builder interface that allows users to construct search vectors without requiring seed songs.

---

## Overview

The current vibe-dj system requires users to provide seed songs to generate playlists. This exploration proposes a visual interface that lets users describe what they're looking for using intuitive controls like sliders and radar charts, which are then translated into the 50-dimensional feature vectors used by FAISS.

---

## Documents

### [UI Mockups](./ui-mockups.md)

Detailed ASCII/text mockups showing:
- **Primary Interface**: Radar chart with presets panel and results
- **Component Details**: Radar chart states, preset cards, fine-tune sliders
- **Blend Mode**: Interface for mixing two seed songs
- **Results Panel**: Song cards with match scores
- **Alternative Views**: 2D mood quadrant, mobile/compact layout
- **Interaction Flows**: Step-by-step user journeys
- **Color Scheme**: Suggested visual styling
- **Accessibility**: Keyboard navigation, screen reader support

### [Technical Specification](./technical-spec.md)

Implementation details including:
- **Feature Vector Structure**: How 50 dimensions map to UI controls
- **UI-to-Feature Mapping**: Conversion formulas for each slider
- **Complete Vector Builder**: Python class for generating query vectors
- **Preset Definitions**: Pre-configured parameter sets (Party, Chill, Workout, etc.)
- **Blend Mode Implementation**: Algorithm for mixing two song vectors
- **API Endpoint Specification**: REST API contracts
- **Library Statistics Caching**: Performance optimization
- **Match Score Calculation**: Converting FAISS distances to percentages
- **Radar Chart Coordinates**: Polar coordinate mapping for visualization

---

## Key Concepts

### Simplified Feature Groups

The 50-dimensional vector is abstracted into 7 user-friendly dimensions:

| UI Control | Feature Indices | Description |
|------------|-----------------|-------------|
| **Tempo** | 45 | Slow ↔ Fast (60-180 BPM) |
| **Energy** | 46, 48 | Calm ↔ Intense (loudness + danceability) |
| **Brightness** | 47 | Warm ↔ Bright (spectral centroid) |
| **Acoustic** | 49 | Electronic ↔ Organic |
| **Danceability** | 48 | Ambient ↔ Groovy |
| **Complexity** | 0-12 | Simple ↔ Complex (MFCC variance) |
| **Harmonic Richness** | 13-24 | Sparse ↔ Rich (chroma energy) |

### Importance Weights

Each dimension has an "importance" setting:
- **Ignore**: Use library average (dimension doesn't affect search)
- **Flexible**: Slight preference for target value
- **Moderate**: Balanced consideration
- **Strict**: Strong preference, heavily weighted in search

### Presets

Quick-start configurations for common use cases:
- 🎉 **Party**: Fast, loud, danceable
- 😌 **Chill**: Slow, soft, acoustic
- 🏃 **Workout**: Fast, high energy
- 🎸 **Acoustic**: Organic, warm
- 🤖 **Electronic**: Synthetic, bright
- 🎹 **Jazz**: Complex, harmonically rich

---

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Implement `LibraryStats` computation and caching
- [ ] Implement `QueryVectorBuilder` class
- [ ] Add API endpoints for visual queries

### Phase 2: Basic UI
- [ ] Implement slider controls for all 7 dimensions
- [ ] Add preset buttons
- [ ] Display results with match scores

### Phase 3: Advanced UI
- [ ] Implement radar chart visualization
- [ ] Add importance weight controls
- [ ] Implement blend mode

### Phase 4: Polish
- [ ] Add 2D mood quadrant alternative view
- [ ] Mobile-responsive layout
- [ ] Accessibility improvements

---

## Dependencies

The visual query builder requires:
- Pre-computed library statistics (mean/std for each dimension)
- Frontend framework (React recommended)
- Charting library for radar chart (Chart.js, D3.js, or Recharts)

---

## Related Documentation

- [Feature Vector Composition](../interesting_queries.md) - What the 50 dimensions represent
- [Query Feasibility Analysis](../interesting_queries_feasibility.md) - What queries are possible
- [Enhanced Audio Features](../enhanced-audio-features.md) - Future feature extraction improvements
