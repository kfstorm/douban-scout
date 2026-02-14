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
- **API Throttling**: Configurable rate limiting to protect the service

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

<!-- ENV_VARS_START -->

| Environment Variable | Default Value | Description |
| -------------------- | ------------- | ----------- |
| `DATABASE_DIR` | `data` | Directory containing the database file |
| `IMPORT_API_KEY` | *None* | Secret key required for import API authentication |
| `RATE_LIMIT_DEFAULT` | `100/minute` | Global default rate limit |
| `RATE_LIMIT_SEARCH` | `30/minute` | Limit for search and movie list endpoints |
| `RATE_LIMIT_GENRES` | `20/minute` | Limit for genres endpoint |
| `RATE_LIMIT_STATS` | `10/minute` | Limit for stats endpoint |
| `RATE_LIMIT_POSTER` | `200/minute` | Limit for poster proxy endpoint |
| `RATE_LIMIT_IMPORT` | `5/minute` | Limit for data import endpoints |

<!-- ENV_VARS_END -->

### Rate Limit Format

Rate limit strings follow the format `[count]/[time_period]`. Examples:

- `10/minute`
- `500/hour`
- `1/second`

Supported time periods: `second`, `minute`, `hour`, `day`, `month`, `year`.

## Troubleshooting

- **Import fails**: Ensure the source file path is correct and accessible to the backend process.
- **No data shown**: Ensure the import process has completed.
- **Port Conflict**: Ensure ports 3000 (Frontend) and 8000 (Backend) are not in use.

## License

MIT License
