# Backend Development Guide

This backend uses `uv` for fast Python package management, `ruff` for linting/formatting, and `mypy` for type checking.

## Quick Start

```bash
cd backend

# Install dependencies (including dev dependencies)
uv sync

# Run the development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Available Commands

### Linting & Formatting

```bash
# Check all linting and type issues
./scripts/lint.sh

# Auto-fix linting issues and format code
./scripts/format.sh
```

### Manual Commands

```bash
# Run ruff linter
uv run ruff check app/

# Run ruff linter with auto-fix
uv run ruff check --fix app/

# Format code with ruff
uv run ruff format app/

# Run type checker
uv run mypy app/

# Run tests
uv run pytest tests/ -v
```

## Project Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── database.py          # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── routers/
│   │   ├── movies.py        # Movie API endpoints
│   │   └── data_import.py   # Import endpoints
│   └── services/
│       ├── movie_service.py # Business logic
│       └── import_service.py # Import processing
├── scripts/
│   ├── lint.sh              # Linting script
│   ├── format.sh            # Formatting script
│   └── test.sh              # Test script
├── pyproject.toml           # Project configuration
├── uv.lock                  # Lock file
└── Dockerfile               # Container definition
```

## Configuration

### Ruff (Linter & Formatter)

Configured in `pyproject.toml`:

- **Target Python version**: 3.11+
- **Line length**: 100 characters
- **Enabled rules**: E, W, F, I, N, D, UP, B, C4, SIM, PTH, PL, PERF, RUF
- **Docstring convention**: Google style

### MyPy (Type Checker)

Configured in `pyproject.toml`:

- **Strict mode enabled**: All functions must have type annotations
- **Missing imports ignored**: For third-party libraries without stubs

## Adding Dependencies

```bash
# Add production dependency
uv add <package>

# Add development dependency
uv add --dev <package>

# Add with version constraint
uv add "<package>>=1.0.0"
```

## Pre-commit Checks

Before committing, run:

```bash
./scripts/lint.sh
```

This ensures:

- Code is properly formatted
- No linting errors
- Type checking passes

## Docker Development

```bash
# Build image
docker build -t douban-backend .

# Run container
docker run -p 8000:8000 -v ./data:/app/data -v ./import:/app/import:ro douban-backend
```

## API Testing

Once the server is running:

```bash
# Health check
curl http://localhost:8000/api/health

# Get movies
curl http://localhost:8000/api/movies

# Get with filters
curl "http://localhost:8000/api/movies?type=movie&min_rating=8.0&genres=剧情,喜剧"

# Get genres
curl http://localhost:8000/api/movies/genres

# Get stats
curl http://localhost:8000/api/movies/stats

# Start import
curl -X POST http://localhost:8000/api/import \
  -H "Content-Type: application/json" \
  -d '{"source_path": "/app/import/backup_20260211_085729.sqlite3"}'

# Check import status
curl http://localhost:8000/api/import/status
```

## Environment Variables

- `DATABASE_URL`: SQLite database path (default: `sqlite:///app/data/movies.db`)
