clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	# /bin/rm -f ./music.db
	#/bin/rm -f ./faiss_index.bin
	/bin/rm -rf ./htmlcov
	/bin/rm -f ./.coverage
	/bin/rm -f ./*.log


install:
	@echo "Installing Dependencies"
	uv sync --all-groups

test:
	uv run pytest tests/unit/ -v

codecov:
	@echo "Creating Code Cov Report"
	uv run pytest --cov-report html:htmlcov --cov=vibe_dj tests/

lint:
	@echo "Linting"
	uv run ruff check --select I --fix .

format:
	@echo "Formatting"
	uv run ruff format .
