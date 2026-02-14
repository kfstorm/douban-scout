# Douban Movie Explorer

A modern web application for exploring Douban movies and TV shows with powerful filtering and search capabilities.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **Card Grid View**: Beautiful poster cards with ratings and genres
- **Advanced Filtering**:
  - Type: Movie / TV / All
  - Rating range (0-10)
  - Minimum rating count
  - 32 genres with AND logic
- **Sorting**: By rating, rating count, year, or title
- **Search**: Real-time title search with debounce
- **Infinite Scroll**: Smooth loading experience
- **Dark Mode**: Toggle between light and dark themes
- **Mobile Responsive**: Optimized for all screen sizes
- **Data Import**: Runtime import from SQLite backup files

## Quick Start

### Prerequisites

- **Node.js**: v18 or later
- **Python**: v3.11 or later
- **uv**: Fast Python package manager ([Installation Guide](https://github.com/astral-sh/uv))

### 1. Start Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

### 2. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Access the Application

- **Web UI**: [http://localhost:3000](http://localhost:3000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Data Import

The application supports importing from Douban backup SQLite files at runtime.

Trigger import via API by providing the absolute path to your Douban backup SQLite file:

```bash
curl -X POST http://localhost:8000/api/import \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"source_path": "/absolute/path/to/your/backup.sqlite3"}'
```

Check progress:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/import/status
```

*Note: Import runs in the background. Existing data in the database will be replaced.*

## Configuration

The backend behavior can be customized using environment variables:

- `DATABASE_DIR`: Directory containing the SQLite database file (default: `data`).
- `IMPORT_API_KEY`: Secret key required for import API authentication.

## Troubleshooting

- **Import fails**: Ensure the source file path is correct and accessible to the backend process.
- **No data shown**: Ensure the import process has completed.
- **Port Conflict**: Ensure ports 3000 (Frontend) and 8000 (Backend) are not in use.

## License

MIT License
