# Development

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

## Prerequisites

- Python 3.14
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Node v24](https://nodejs.org/en/download)

## Setup

```bash
# Clone the repository
git clone <repository-url>
cd vibe-dj

# Setup virtual environment
uv venv

# Install dependencies
make install

# Run unit tests
make test

# Start server - Accessible at http://localhost:8000
make run

# You can run the API and UI servers separately
# Start API server - Accessible at http://localhost:8000
make api-server

# Start UI development server - Accessible at http://localhost:5173
make ui-server
```

## Docker

```bash
# Build the Docker image
docker build -f Dockerfile -t vibe-dj .
```
