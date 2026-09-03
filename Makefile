.PHONY: help install test lint format clean doctor

help:
	@echo "FireTwin Development Commands"
	@echo "=============================="
	@echo "make install    - Create conda environment and install package"
	@echo "make test       - Run tests with pytest"
	@echo "make lint       - Run linters (ruff, mypy)"
	@echo "make format     - Format code with ruff"
	@echo "make clean      - Remove build artifacts and caches"
	@echo "make doctor     - Run system diagnostics"
	@echo "make pre-commit - Install pre-commit hooks"

install:
	conda env create -f environment.yml
	conda run -n firetwin pip install -e .
	@echo "Environment created! Activate with: conda activate firetwin"

test:
	pytest tests/ -v --cov=firetwin --cov-report=term-missing

lint:
	ruff check src tests
	ruff format --check src tests
	mypy src --ignore-missing-imports

format:
	ruff format src tests
	ruff check --fix src tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf build/
	rm -rf dist/

doctor:
	firetwin doctor

pre-commit:
	pre-commit install
	@echo "Pre-commit hooks installed!"
