# AGENTS.md - Douban Movie Explorer

This document provides guidelines for AI agents working on this codebase.

## Project Overview

A modern web application for exploring Douban movies and TV shows:
- **Backend**: FastAPI + SQLite + SQLAlchemy
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **State Management**: TanStack Query (data) + Zustand (filter state)
- **Database**: Optimized SQLite with indexes for filtering/sorting

## Build Commands

### Backend (Python)

```bash
cd backend

# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with custom database
DATABASE_URL=sqlite:///data/movies.db uv run uvicorn app.main:app --reload

# Lint and format
bash scripts/lint.sh      # ruff check + mypy
bash scripts/format.sh    # auto-format with ruff
bash scripts/test.sh      # run all tests

# Single test
PYTHONPATH=. uv run pytest tests/test_api.py::TestMoviesEndpoint::test_get_movies_with_data -v

# Run specific test file
PYTHONPATH=. uv run pytest tests/test_api.py -v
```

### Frontend (TypeScript/React)

```bash
cd frontend

# Install dependencies
npm install

# Run development server (port 3000, proxies /api to backend:8000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d --build
```

## Code Style Guidelines

### Python (Backend)

**Imports**
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

**Formatting**
- Line length: 100 characters
- Indent: 4 spaces
- Quote style: double quotes
- No trailing commas
- LF line endings

**Type Hints**
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

**Naming Conventions**
- Classes: `PascalCase` (e.g., `MovieService`, `ImportService`)
- Functions/variables: `snake_case` (e.g., `get_movies`, `movie_service`)
- Constants: `UPPER_SNAKE_CASE` or `ClassVar` sets
- Private methods: `_leading_underscore`
- Type variables: `PascalCase` (e.g., `T`, `K`, `V`)

**Error Handling**
- Use FastAPI's `HTTPException` for API errors
- Log exceptions with `logger.exception()` for errors
- Validate inputs with Pydantic models
- Return proper HTTP status codes (404 for not found, 422 for validation)

**Logging**
- Configure logging in `app/logging_config.py`
- Use module-specific loggers:

```python
logger = logging.getLogger("douban.movies")
logger.info("Querying movies with filters: %s", filters)
logger.error("Failed to import: %s", e, exc_info=True)
```

### TypeScript/React (Frontend)

**Imports**
- Use absolute imports for internal modules
- Separate imports by type: React → external libraries → internal components/hooks

```typescript
import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

import { MovieGrid } from './components/MovieGrid';
import { FilterSidebar } from './components/FilterSidebar';
import { useFilterStore } from './store/useFilterStore';
import { moviesApi, type MoviesParams } from './services/api';
```

**TypeScript Configuration**
- `strict: true` enabled in `tsconfig.json`
- Enable: `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`
- Use `.tsx` for React components, `.ts` for utilities

**Component Patterns**
- Functional components with hooks
- Type props with TypeScript interfaces
- Use TanStack Query for server state
- Use Zustand for client state (filters, theme)

```typescript
interface MovieCardProps {
  movie: Movie;
  onClick?: (movie: Movie) => void;
}

export function MovieCard({ movie, onClick }: MovieCardProps) {
  return (
    <div className="movie-card" onClick={() => onClick?.(movie)}>
      <img src={movie.poster_url} alt={movie.title} />
    </div>
  );
}
```

**Naming Conventions**
- Components: `PascalCase` (e.g., `MovieGrid`, `FilterSidebar`)
- Files: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Hooks: `camelCase` starting with `use` (e.g., `useDebounce`)
- State stores: `useStoreName` (e.g., `useFilterStore`)

**Tailwind CSS**
- Use utility classes for styling
- Support dark mode with `dark:` prefix
- Responsive design with `sm:`, `md:`, `lg:` prefixes

```tsx
<div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
  <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg">
    Click me
  </button>
</div>
```

## Database (SQLAlchemy)

- Use SQLAlchemy 2.0 patterns
- Models in `app/database.py`
- Schemas in `app/schemas.py`
- Services in `app/services/`
- Use dependency injection for sessions:

```python
from app.database import get_db

@app.get("/movies")
def get_movies(db: Session = Depends(get_db)) -> MoviesListResponse: ...
```

## Testing

**Backend (pytest)**
- Tests in `backend/tests/`
- Fixtures in `conftest.py`
- Use temporary directories (`tempfile.TemporaryDirectory`) for isolation
- Follow `test_*.py` and `Test*` conventions
- Tests must use autouse fixtures for database isolation

**Frontend (not configured)**
- No test framework configured yet
- If adding tests, use Vitest or Jest with React Testing Library

## Linting & Type Checking

**Backend (ruff + mypy)**

```bash
# Check ruff
ruff check .

# Auto-fix ruff
ruff check --fix .

# Check mypy
mypy app/
```

Rules enabled: E, W, F, I, N, D (google), UP, B, C4, SIM, PTH, PL, PERF, RUF

**Frontend (TypeScript)**

```bash
# Type check (runs as part of build)
npm run build

# No ESLint configured yet
```

## File Structure

```
douban-movie-explorer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── database.py          # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── logging_config.py    # Logging setup
│   │   ├── routers/             # API endpoints
│   │   │   ├── movies.py
│   │   │   └── data_import.py
│   │   └── services/            # Business logic
│   │       ├── movie_service.py
│   │       └── import_service.py
│   ├── scripts/                 # Dev scripts
│   │   ├── lint.sh
│   │   ├── format.sh
│   │   └── test.sh
│   ├── tests/                   # Unit tests
│   │   ├── conftest.py
│   │   ├── test_api.py
│   │   └── test_services.py
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── MovieGrid.tsx
│   │   │   ├── FilterSidebar.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   └── ...
│   │   ├── hooks/               # Custom hooks
│   │   ├── services/            # API services
│   │   │   └── api.ts
│   │   ├── store/              # Zustand stores
│   │   │   └── useFilterStore.ts
│   │   ├── types/              # TypeScript types
│   │   │   └── movie.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
├── data/                        # SQLite database
├── import/                       # Source SQLite files for import
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

## Git Commit Style

- Format: `[scope] message`
- Scopes: `backend`, `frontend`, `docs`, `infra`
- Example: `[backend] add unit tests for API`

## Environment Variables

**Backend**
- `DATABASE_URL`: SQLite connection string (default: `sqlite:///data/movies.db`)

**Frontend**
- `VITE_API_URL`: Backend API URL (default: `/api`)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/movies` | List movies with filters |
| GET | `/api/movies/genres` | Get genres with counts |
| GET | `/api/movies/stats` | Get database statistics |
| POST | `/api/import` | Start data import |
| GET | `/api/import/status` | Get import progress |

## Key Patterns

### Backend Filter Logic
- Genre filtering uses AND logic (movie must have ALL specified genres)
- Cursor-based pagination for performance
- Rating range: 0-10 inclusive
- Limit: 1-100 per page

### Frontend State
- Zustand for filter state (persisted to localStorage)
- TanStack Query for API data (caching, refetching)
- Dark mode toggle with system preference detection

### Import Process
- Background thread import (non-blocking)
- Batch processing (1000 records per transaction)
- Clears existing data before import
- Progress polling via `/api/import/status`
