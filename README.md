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

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **SQLite**: Optimized database with indexes
- **Pydantic**: Data validation

### Frontend
- **React 18**: Component-based UI
- **TypeScript**: Type safety
- **Tailwind CSS**: Utility-first styling
- **TanStack Query**: Data fetching and caching
- **Zustand**: State management
- **Headless UI**: Accessible components

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Static file serving and reverse proxy

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Or: Python 3.11+ and Node.js 20+

### Docker Deployment (Recommended)

1. **Clone the repository**:
```bash
git clone <repository-url>
cd douban-movie-explorer
```

2. **Prepare data**:
```bash
# Copy your Douban backup SQLite file to import folder
cp /path/to/backup_*.sqlite3 import/
```

3. **Start services**:
```bash
docker-compose up -d
```

4. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- API Docs: http://localhost:8000/docs

5. **Import data**:
```bash
# Trigger import via API
curl -X POST http://localhost:8000/api/import \
  -H "Content-Type: application/json" \
  -d '{"source_path": "/app/import/backup_*.sqlite3"}'
```

Or check import status:
```bash
curl http://localhost:8000/api/import/status
```

### Development Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app.database import init_db; init_db()"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will be available at http://localhost:3000 and proxy API requests to the backend.

## API Endpoints

### Movies

- `GET /api/movies` - List movies with filters
  - Query params: `cursor`, `limit`, `type`, `min_rating`, `max_rating`, `min_rating_count`, `genres`, `search`, `sort_by`, `sort_order`
- `GET /api/movies/genres` - Get all genres with counts
- `GET /api/movies/stats` - Get database statistics

### Import

- `POST /api/import` - Start importing from SQLite file
- `GET /api/import/status` - Get import progress

### Health

- `GET /api/health` - Health check

## Data Import

The application supports importing from Douban backup SQLite files at runtime.

### Import Process

1. Place your `.sqlite3` file in the `import/` directory
2. Call the import API endpoint
3. Monitor progress via status endpoint
4. Import runs asynchronously in the background
5. Existing data is replaced (clean slate)

### Import Example

```bash
# Start import
curl -X POST http://localhost:8000/api/import \
  -H "Content-Type: application/json" \
  -d '{"source_path": "/app/import/backup_20240211_085729.sqlite3"}'

# Check status
curl http://localhost:8000/api/import/status
```

### Import Performance

- **738k records**: ~5-10 minutes
- **Batch size**: 1000 records per transaction
- **Memory efficient**: Streaming read from source

## Database Schema

### Optimized Schema

```sql
-- Main movies table
CREATE TABLE movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    douban_id VARCHAR(16) UNIQUE NOT NULL,
    imdb_id VARCHAR(16),
    title VARCHAR(256) NOT NULL,
    year INTEGER,
    rating FLOAT,
    rating_count INTEGER DEFAULT 0,
    type VARCHAR(16),
    poster_url TEXT,
    douban_url TEXT NOT NULL
);

-- Genre junction table (many-to-many)
CREATE TABLE movie_genres (
    movie_id INTEGER REFERENCES movies(id) ON DELETE CASCADE,
    genre VARCHAR(32),
    PRIMARY KEY (movie_id, genre)
);
```

### Indexes

- `idx_movies_type` - Type filtering
- `idx_movies_rating` - Rating range queries
- `idx_movies_rating_count` - Minimum rating count
- `idx_movies_year` - Year sorting
- `idx_movie_genres_genre` - Genre filtering

## Available Genres

The application supports 32 genres:

1. 剧情 (Drama)
2. 喜剧 (Comedy)
3. 爱情 (Romance)
4. 动作 (Action)
5. 惊悚 (Thriller)
6. 犯罪 (Crime)
7. 恐怖 (Horror)
8. 动画 (Animation)
9. 纪录片 (Documentary)
10. 短片 (Short)
11. 悬疑 (Mystery)
12. 冒险 (Adventure)
13. 科幻 (Sci-Fi)
14. 奇幻 (Fantasy)
15. 家庭 (Family)
16. 音乐 (Music)
17. 历史 (History)
18. 战争 (War)
19. 歌舞 (Musical)
20. 传记 (Biography)
21. 古装 (Costume)
22. 真人秀 (Reality TV)
23. 同性 (LGBT)
24. 运动 (Sport)
25. 西部 (Western)
26. 情色 (Erotic)
27. 儿童 (Children)
28. 武侠 (Wuxia)
29. 脱口秀 (Talk Show)
30. 黑色电影 (Film Noir)
31. 戏曲 (Opera)
32. 灾难 (Disaster)

## Configuration

### Environment Variables

#### Backend
- `DATABASE_URL`: SQLite database path (default: `sqlite:///data/movies.db`)

#### Frontend
- `VITE_API_URL`: Backend API URL (default: `/api`)

### Docker Volumes

- `./data`: Application database storage
- `./import`: Read-only mount for source SQLite files

## Development

### Project Structure

```
douban-movie-explorer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── database.py          # Database connection
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── movies.py        # Movie API endpoints
│   │   │   └── data_import.py   # Import API endpoints
│   │   └── services/
│   │       ├── movie_service.py # Business logic
│   │       └── import_service.py # Import processing
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom hooks
│   │   ├── services/            # API services
│   │   ├── store/               # Zustand stores
│   │   ├── types/               # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── README.md
```

### Building for Production

```bash
# Build and start production containers
docker-compose -f docker-compose.prod.yml up -d --build
```

### Troubleshooting

**Import fails with "Source file not found"**
- Ensure the SQLite file is in the `import/` directory
- Check the path is correct in the API call

**Frontend shows "Loading failed"**
- Check backend is running: `curl http://localhost:8000/api/health`
- Check browser console for CORS errors

**Slow queries**
- Ensure database indexes are created
- Check import completed successfully

## License

MIT License

## Acknowledgments

- Data sourced from Douban
- Built with FastAPI, React, and Tailwind CSS
