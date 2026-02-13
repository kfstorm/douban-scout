# Douban Movie Explorer - Root

This file provides high-level project information. For detailed coding guidelines, check subdirectory-specific AGENTS.md files.

## Project Overview

A modern web application for exploring Douban movies and TV shows:
- **Backend**: FastAPI + SQLite + SQLAlchemy
- **Frontend**: React 18 + TypeScript + Tailwind CSS

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
└── frontend/                    # React/TypeScript frontend
```
