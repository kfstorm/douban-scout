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

### 3. Access the application
- Web UI: http://localhost:3000
- API Docs: http://localhost:8000/docs

### 4. Import your data
Trigger import via API by providing the absolute path to your Douban backup SQLite file:
```bash
curl -X POST http://localhost:8000/api/import \
  -H "Content-Type: application/json" \
  -d '{"source_path": "/absolute/path/to/your/backup.sqlite3"}'
```

Check progress:
```bash
curl http://localhost:8000/api/import/status
```

## Data Import

The application supports importing from Douban backup SQLite files at runtime.
- **Async Process**: Import runs in the background.
- **Clean Slate**: Existing data is replaced.
- **Performance**: Optimized for large datasets (e.g., 700k+ records).

## Troubleshooting

- **Import fails**: Ensure the source file path is correct and accessible to the backend.
- **No data shown**: Ensure the import process has completed.
- **Port Conflict**: Ensure ports 3000 and 8000 are not in use.

## License

MIT License
