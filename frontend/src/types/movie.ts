export interface Movie {
  id: number;
  title: string;
  year: number | null;
  rating: number | null;
  rating_count: number;
  type: 'movie' | 'tv';
  genres: string[];
  regions: string[];
  updated_at: number | null;
}

export interface MoviesListResponse {
  items: Movie[];
  next_cursor: string | null;
  total: number;
}

export interface GenreCount {
  genre: string;
  count: number;
}

export interface RegionCount {
  region: string;
  count: number;
}

export interface StatsResponse {
  total_movies: number;
  total_tv: number;
  avg_rating: number;
  total_genres: number;
  total_regions: number;
}

export interface ImportStatus {
  status: 'idle' | 'running' | 'completed' | 'failed';
  processed: number;
  total: number;
  percentage: number;
  message: string | null;
  started_at: string | null;
  completed_at: string | null;
}
