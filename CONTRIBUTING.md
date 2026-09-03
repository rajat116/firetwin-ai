# Contributing to FireTwin

Thank you for your interest in contributing to FireTwin!

## Development Setup

1. **Fork and clone** the repository:
```bash
git clone https://github.com/YOUR_USERNAME/firetwin-ai.git
cd firetwin-ai
```

2. **Create conda environment**:
```bash
conda env create -f environment.yml
conda activate firetwin
```

3. **Install package in development mode**:
```bash
pip install -e .
```

4. **Install pre-commit hooks**:
```bash
pre-commit install
```

5. **Run tests**:
```bash
make test
```

## Development Workflow

1. **Create a feature branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**:
   - Write code following the style guide (see below)
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**:
```bash
make lint    # Check code style
make format  # Auto-format code
make test    # Run test suite
```

4. **Commit your changes**:
```bash
git add .
git commit -m "Brief description of changes"
```

Pre-commit hooks will automatically:
- Format code with Ruff
- Check for common issues
- Run type checking with MyPy

5. **Push and create PR**:
```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

### Python

- **Formatter**: Ruff (line length 100)
- **Linter**: Ruff with project-specific rules
- **Type hints**: Encouraged but not strictly required
- **Docstrings**: Use Google style for public functions

Example:
```python
def calculate_fire_probability(
    terrain: np.ndarray,
    weather: dict,
    fuel_type: int,
) -> float:
    """Calculate probability of fire spread.

    Args:
        terrain: Elevation grid in meters
        weather: Dictionary with wind_speed, temperature, humidity
        fuel_type: LANDFIRE fuel model code

    Returns:
        Probability of spread (0-1)

    Raises:
        ValueError: If fuel_type is invalid
    """
    ...
```

### Naming Conventions

- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Prefix with `_`

### Imports

Group and sort imports:
```python
# Standard library
import os
from pathlib import Path

# Third-party
import numpy as np
import pandas as pd
from pydantic import BaseModel

# Local
from firetwin.data import load_firms_data
from firetwin.models import BaselineModel
```

## Testing

### Test Structure

```
tests/
├── unit/              # Fast, isolated tests
├── integration/       # Multi-component tests
├── data_contracts/    # Data validation tests
└── leakage/           # Temporal leakage prevention tests
```

### Writing Tests

```python
import pytest
from firetwin.geo import reproject_raster


def test_reproject_raster_preserves_shape():
    """Test that reprojection maintains array shape."""
    input_array = np.random.rand(100, 100)
    result = reproject_raster(
        input_array,
        src_crs="EPSG:4326",
        dst_crs="EPSG:3857"
    )
    assert result.shape == input_array.shape


@pytest.mark.slow
def test_download_firms_data():
    """Test FIRMS API client (requires network)."""
    ...
```

### Running Tests

```bash
# All tests
pytest

# Specific category
pytest tests/unit -v

# Skip slow tests
pytest -m "not slow"

# With coverage
pytest --cov=firetwin --cov-report=html
```

## Documentation

### Docstring Requirements

All public functions, classes, and modules should have docstrings.

### README Updates

When adding significant features:
1. Update the feature list
2. Add usage examples
3. Update roadmap status

### Technical Documentation

For major decisions:
1. Record in `docs/DECISIONS.md`
2. Include context, alternatives, and rationale

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally
- [ ] Code is formatted and linted
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] No credentials or large files committed

### PR Description

Include:
1. **What**: Brief summary of changes
2. **Why**: Motivation and context
3. **How**: Approach taken
4. **Testing**: How you verified the changes
5. **Screenshots**: If UI/UX changes

Example:
```markdown
## What
Add FIRMS API client for active fire data retrieval

## Why
Phase 2 requires automated fire observation downloads

## How
- Implemented `FirmsClient` with retry logic
- Added Pydantic schema for response validation
- Cached responses to avoid rate limits

## Testing
- Unit tests with mocked API responses
- Integration test with real API (requires key)
- Tested with 3 historical fires

## Notes
Requires FIRMS_MAP_KEY in .env
```

### Review Process

1. Automated CI checks must pass
2. At least one maintainer review required
3. Address feedback and update PR
4. Maintainer will merge when ready

## Reporting Issues

### Bug Reports

Include:
1. **Environment**: OS, Python version, conda env
2. **Steps to reproduce**: Minimal example
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Error messages**: Full traceback

### Feature Requests

Include:
1. **Use case**: What problem does this solve?
2. **Proposed solution**: How should it work?
3. **Alternatives**: Other approaches considered?
4. **Impact**: Who benefits? How urgent?

## Code of Conduct

### Our Standards

- Be respectful and constructive
- Focus on what's best for the project
- Accept feedback gracefully
- Provide thoughtful, helpful reviews

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks
- Publishing others' private information
- Unprofessional conduct

## Questions?

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Open an Issue
- **Security concerns**: See SECURITY.md
- **Direct contact**: rajatgupta116@gmail.com

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
