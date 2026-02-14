# Stage 1: Build the React UI
FROM node:20-alpine AS ui-builder

WORKDIR /ui

# Copy package files and install dependencies
COPY ui/package*.json ./
RUN npm ci

# Copy UI source and build
COPY ui/ ./
RUN npm run build

# Stage 2: Install Python dependencies
FROM python:3.14.2-slim AS py-builder

WORKDIR /app

# Install uv for fast dependency installation
RUN pip install --no-cache-dir uv

# Copy project files and install dependencies (non-editable)
COPY pyproject.toml uv.lock* README.md ./
COPY src/ ./src/
RUN uv pip install --system --no-cache .

# Stage 3: Final runtime image
FROM python:3.14.2-slim

# Install system dependencies required by librosa and audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    libmpg123-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages and binaries from builder
COPY --from=py-builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=py-builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

# Set working directory
WORKDIR /app

# Copy built UI from the first stage
COPY --from=ui-builder /ui/dist ./ui/dist

# Create directories for persistent data
RUN mkdir -p /data /music

# Set environment variables for data paths
ENV VIBE_DJ_DATA_DIR=/data
ENV VIBE_DJ_DATABASE_PATH=/data/music.db
ENV VIBE_DJ_FAISS_INDEX_PATH=/data/faiss_index.bin
ENV VIBE_DJ_UI_PATH=/app/ui/dist

# Set the working directory to /data so database and index files are created there
WORKDIR /data

# Expose port for FastAPI
EXPOSE 8000

# Entry point is uvicorn running the FastAPI app
ENTRYPOINT ["uvicorn", "vibe_dj.app:app", "--host", "0.0.0.0", "--port", "8000"]

# Default command (can be overridden)
CMD []
