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

```text
douban-movie-explorer/
├── backend/                     # Python/FastAPI backend
├── frontend/                    # React/TypeScript frontend
└── scripts/                     # Project-wide scripts
```

## Development Workflow

### Pre-commit Hooks

This project uses `pre-commit` to ensure code quality. The hooks run linting for Markdown, Python, and TypeScript, as well as backend unit tests.

To set up the hooks:

```bash
scripts/setup-hooks.sh
```

Note: You must have `pre-commit` installed on your system (`pip install pre-commit` or `brew install pre-commit`).

### Auto-fixing Problems

If you encounter linting or formatting issues, you can run the following tool to automatically fix most problems:

```bash
scripts/fix-all.sh
```

This script handles:

- Backend: Ruff check (fix) and format
- Frontend: ESLint fix and Prettier format
- Markdown: markdownlint-cli2 fix
