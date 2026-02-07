# Use Python 3.13 as base (3.14 not widely available yet in Docker images)
FROM python:3.14.2-slim

# Install system dependencies required by librosa and audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    libmpg123-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/
COPY README.md ./

# Install uv package manager for faster dependency installation
RUN pip install --no-cache-dir uv

# Install project dependencies
RUN uv pip install --system --no-cache -e .

# Create directories for persistent data
RUN mkdir -p /data /music

# Set environment variables for data paths
ENV VIBE_DJ_DATA_DIR=/data

# Set the working directory to /data so database and index files are created there
WORKDIR /data

# Entry point is the vibe-dj CLI
ENTRYPOINT ["vibe-dj"]

# Default command shows help
CMD ["--help"]
