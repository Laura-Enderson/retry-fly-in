run:
	uv run python -m src

install:
	@uv sync

debug:
	@uv run python -m pdb -m src

clean:
	@rm -rf .mypy_cache
	@rm -rf src/__pycache__ src/tools/__pycache__ src/TUI/__pycache__
	@rm -rf src/GUI/__pycache__

fclean: clean
	@rm -rf .venv

lint:
	@uv run flake8 ./src
	@uv run mypy ./src --warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs

lint-strict:
	@uv run flake8 ./src
	@uv run mypy ./src --strict

.PHONY: install run debug clean lint lint-strict