# Douban Movie Explorer - Root

This file provides high-level project information. For detailed coding guidelines, check subdirectory-specific AGENTS.md files.

## Project Overview

A modern web application for exploring Douban movies and TV shows:
- **Backend**: FastAPI + SQLite + SQLAlchemy
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **State Management**: TanStack Query (data) + Zustand (filter state)
- **Database**: Optimized SQLite with indexes for filtering/sorting

## Subdirectory-Specific Rules

When working on a specific part of the codebase, see the dedicated AGENTS.md file:

- **Backend work** → See `backend/AGENTS.md` for Python/FastAPI rules
- **Frontend work** → See `frontend/AGENTS.md` for React/TypeScript rules

## Project-Wide Guidelines

### Git Commit Style

- Format: `[scope] message`
- Scopes: `backend`, `frontend`, `docs`, `infra`
- Example: `[backend] add unit tests for API`

### File Structure

```
douban-movie-explorer/
├── backend/                     # Python/FastAPI backend
│   ├── app/                     # Application code
│   ├── scripts/                 # Dev scripts
│   ├── tests/                   # Unit tests
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                    # React/TypeScript frontend
│   ├── src/                     # Source code
│   ├── package.json
│   └── vite.config.ts
├── data/                        # SQLite database
├── import/                      # Source SQLite files for import
├── docker-compose.yml
└── docker-compose.prod.yml
```

### Environment Variables

**Backend**
- `DATABASE_URL`: SQLite connection string (default: `sqlite:///data/movies.db`)

**Frontend**
- `VITE_API_URL`: Backend API URL (default: `/api`)

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/movies` | List movies with filters |
| GET | `/api/movies/genres` | Get genres with counts |
| GET | `/api/movies/stats` | Get database statistics |
| POST | `/api/import` | Start data import |
| GET | `/api/import/status` | Get import progress |

### Docker Commands

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d --build
```

### Key Patterns

#### Backend Filter Logic
- Genre filtering uses AND logic (movie must have ALL specified genres)
- Cursor-based pagination for performance
- Rating range: 0-10 inclusive
- Limit: 1-100 per page

#### Frontend State
- Zustand for filter state (persisted to localStorage)
- TanStack Query for API data (caching, refetching)
- Dark mode toggle with system preference detection

#### Import Process
- Background thread import (non-blocking)
- Batch processing (1000 records per transaction)
- Clears existing data before import
- Progress polling via `/api/import/status`
