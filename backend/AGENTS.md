# AGENTS.md - Backend

> For project overview and high-level information, see [../AGENTS.md](../AGENTS.md)

This document provides guidelines for AI agents working on the **backend** codebase (FastAPI + Python).

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy 2.0
- **ORM**: SQLAlchemy
- **Throttling**: slowapi (configurable via pydantic-settings)
- **Testing**: pytest
- **Linting**: ruff + mypy
- **Package Manager**: uv

## Build Commands

```bash
# Navigate to backend directory (all commands assume you're in backend/)
cd backend

# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with custom data directory
DATA_DIR=custom_data uv run uvicorn app.main:app --reload

# Lint and format
scripts/lint.sh      # ruff check + mypy
scripts/format.sh    # auto-format with ruff
scripts/test.sh      # run all tests

# Single test
uv run pytest tests/test_api.py::TestMoviesEndpoint::test_get_movies_with_data -v

# Run specific test file
uv run pytest tests/test_api.py -v
```

## Environment Variables

See the [main README.md](../README.md#configuration) for the full list of configurable environment variables.

## Code Style Guidelines

### Imports

- Use isort ordering (`ruff` auto-sorts)
- Group: standard library → third-party → first-party
- Known first-party module: `app`

```python
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.database import Movie, MovieGenre
from app.schemas import MovieResponse
```

### Formatting

- Line length: 100 characters
- Indent: 4 spaces
- Quote style: double quotes
- No trailing commas
- LF line endings

### Type Hints

- **Strict mode enabled** (`disallow_untyped_defs: true`)
- All function parameters and returns must have type annotations
- Use `| None` syntax (not `Optional[]`)
- Use `ClassVar[T]` for class constants
- Import types from `typing` or `typing_extensions`

```python
def get_movies(
    db: Session,
    cursor: str | None = None,
    limit: int = 20,
    type: Literal["movie", "tv"] | None = None,
) -> MoviesListResponse: ...
```

### Naming Conventions

- Classes: `PascalCase` (e.g., `MovieService`, `ImportService`)
- Functions/variables: `snake_case` (e.g., `get_movies`, `movie_service`)
- Constants: `UPPER_SNAKE_CASE` or `ClassVar` sets
- Private methods: `_leading_underscore`
- Type variables: `PascalCase` (e.g., `T`, `K`, `V`)

### Error Handling

- Use FastAPI's `HTTPException` for API errors
- Log exceptions with `logger.exception()` for errors
- Validate inputs with Pydantic models
- Return proper HTTP status codes (404 for not found, 422 for validation)

### Logging

- Configure logging in `app/logging_config.py`
- Use module-specific loggers:

```python
logger = logging.getLogger("douban.movies")
logger.info("Querying movies with filters: %s", filters)
logger.error("Failed to import: %s", e, exc_info=True)
```

## API Endpoints & Security

### Throttling (Rate Limiting)

All public endpoints **must** have rate limiting applied using the `limiter` instance from `app.limiter`.

- Use `@limiter.limit(settings.rate_limit_...)` decorator.
- Thresholds should be configurable in `app/config.py` via `Settings`.
- The endpoint function **must** accept a `Request` object as its first argument for the limiter to work.

Example:

```python
from fastapi import Request
from app.config import settings
from app.limiter import limiter

@router.get("/my-endpoint")
@limiter.limit(settings.rate_limit_default)
def my_endpoint(request: Request):
    ...
```

### Authentication

Endpoints that perform administrative actions (like data modification or import) **must** be protected.

- Use the `verify_api_key` dependency from `app.dependencies.auth`.
- For router-wide protection, add it to the `APIRouter` dependencies.

Example:

```python
from app.dependencies.auth import verify_api_key

router = APIRouter(prefix="/admin", dependencies=[Depends(verify_api_key)])
```

## Database (SQLAlchemy & SQLite)

- Use SQLAlchemy 2.0 patterns
- Models in `app/database.py`
- Schemas in `app/schemas.py`
- Services in `app/services/`
- **Search**: Uses SQLite FTS5 virtual table `movie_search` for optimized title search
- **Concurrency**: Database is served in read-only mode with atomic swaps during import to ensure consistency
- Use dependency injection for sessions:

```python
from app.database import get_db

@app.get("/movies")
def get_movies(db: Session = Depends(get_db)) -> MoviesListResponse: ...
```

## Testing

- Tests in `backend/tests/`
- Fixtures in `conftest.py`
- Use temporary directories (`tempfile.TemporaryDirectory`) for isolation
- Follow `test_*.py` and `Test*` conventions
- Tests must use autouse fixtures for database isolation

### Testing Policy

See [root AGENTS.md](../AGENTS.md#testing-policy) for general testing guidelines.

## Linting & Type Checking

```bash
# Check ruff
ruff check .

# Auto-fix ruff
ruff check --fix .

# Check mypy
mypy app/
```

Rules enabled: E, W, F, I, N, D (google), UP, B, C4, SIM, PTH, PL, PERF, RUF

## File Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── cache.py             # In-memory cache manager
│   ├── database.py          # SQLAlchemy models & connection
│   ├── logging_config.py    # Logging setup
│   ├── main.py              # FastAPI entry point
│   ├── schemas.py           # Pydantic schemas
│   ├── dependencies/        # FastAPI dependencies
│   │   └── auth.py          # API key verification
│   ├── routers/             # API endpoints
│   │   ├── movies.py
│   │   └── data_import.py
│   └── services/            # Business logic
│       ├── movie_service.py
│       ├── import_service.py
│       └── poster_service.py
├── data/                    # Application data directory
│   ├── db/                  # SQLite database
│   └── cache/               # Cached data
│       └── posters/         # Cached poster images
├── scripts/                 # Dev scripts
│   ├── lint.sh
│   ├── format.sh
│   └── test.sh
├── tests/                   # Unit tests
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_services.py
│   └── test_poster_cache.py
├── pyproject.toml
└── uv.lock
```
