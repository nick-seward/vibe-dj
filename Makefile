clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	# /bin/rm -f ./music.db
	#/bin/rm -f ./faiss_index.bin
	/bin/rm -rf ./htmlcov
	/bin/rm -f ./.coverage
	/bin/rm -f ./*.log
	/bin/rm -rf ./ui/dist
	/bin/rm -rf ./ui/node_modules


install:
	@echo "Installing Python Dependencies"
	uv sync --all-groups

	@echo "Installing Node Dependencies"
	cd ui && npm install

test:
	uv run pytest -v

codecov:
	@echo "Creating Code Cov Report"
	uv run pytest --cov-report html:htmlcov --cov=vibe_dj tests/

lint:
	@echo "Linting"
	uv run ruff check --select I --fix .

format:
	@echo "Formatting"
	uv run ruff format .

ui-server:
	@echo "Starting UI development server"
	cd ui && npm run dev

api-server:
	@echo "Starting FastAPI server"
	uv run uvicorn vibe_dj.app:app --host 0.0.0.0 --port 8000 --reload

build-ui:
	@echo "Building UI components"
	cd ui && npm run build

run: build-ui
	@echo "Starting FastAPI server with built UI"
	uv run uvicorn vibe_dj.app:app --host 0.0.0.0 --port 8000
