clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	/bin/rm -f ./music.db
	/bin/rm -rf ./htmlcov
	/bin/rm -f ./.coverage
	/bin/rm -f ./*.log


install:
	@echo "Installing Dependencies"
	uv sync --all-groups
