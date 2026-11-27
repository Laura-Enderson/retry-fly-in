run:
	uv run python fly-in.py

install:
	@uv sync

debug:
	@uv run python -m pdb fly-in.py

clean:
	@rm -rf .mypy_cache
	@rm -rf __pycache__ 

fclean: clean
	@rm -rf .venv

lint:
	@uv run flake8 . --exclude=.venv
	@uv run mypy . --exclude=.venv \
	--warn-return-any \
	--warn-unused-ignores \
	--ignore-missing-imports \
	--disallow-untyped-defs \
	--check-untyped-defs

lint-strict:
	@uv run flake8 . --exclude=.venv
	@uv run mypy . --strict --exclude=.venv

.PHONY: install run debug clean lint lint-strict