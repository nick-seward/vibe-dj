clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	/bin/rm -f ./music.db
	/bin/rm -f ./faiss_index.bin
	/bin/rm -rf ./htmlcov
	/bin/rm -f ./.coverage
	/bin/rm -f ./*.log


install:
	@echo "Installing Dependencies"
	uv sync --all-groups

test:
	uv run pytest tests/unit/ -v

# Docker targets
docker-build:
	docker build -t vibe-dj .

docker-build-compose:
	docker-compose build

docker-index:
	@echo "Usage: make docker-index MUSIC_PATH=/path/to/music"
	@if [ -z "$(MUSIC_PATH)" ]; then \
		echo "Error: MUSIC_PATH not set"; \
		exit 1; \
	fi
	docker run --rm \
		-v $(MUSIC_PATH):/music:ro \
		-v $(PWD)/data:/data \
		vibe-dj index /music

docker-playlist:
	@echo "Generating playlist from data/seeds.json"
	docker run --rm \
		-v $(PWD)/data:/data \
		vibe-dj playlist --seeds-json /data/seeds.json --output /data/playlist.m3u

docker-shell:
	docker run --rm -it \
		-v $(PWD)/data:/data \
		--entrypoint /bin/bash \
		vibe-dj
