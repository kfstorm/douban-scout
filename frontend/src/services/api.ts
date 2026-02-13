import axios from 'axios';
import type { MoviesListResponse, GenreCount, StatsResponse, ImportStatus } from '../types/movie';

const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface MoviesParams {
  cursor?: string;
  limit?: number;
  type?: 'movie' | 'tv';
  min_rating?: number;
  max_rating?: number;
  min_rating_count?: number;
  genres?: string[];
  search?: string;
  sort_by?: 'rating' | 'rating_count' | 'year' | 'title';
  sort_order?: 'asc' | 'desc';
}

export const moviesApi = {
  getMovies: async (params: MoviesParams = {}): Promise<MoviesListResponse> => {
    const response = await api.get('/movies', {
      params: {
        ...params,
        genres: params.genres?.join(','),
      },
    });
    return response.data;
  },

  getGenres: async (type?: 'movie' | 'tv'): Promise<GenreCount[]> => {
    const response = await api.get('/movies/genres', {
      params: { type },
    });
    return response.data;
  },

  getStats: async (): Promise<StatsResponse> => {
    const response = await api.get('/movies/stats');
    return response.data;
  },
};

export const importApi = {
  startImport: async (sourcePath: string): Promise<ImportStatus> => {
    const response = await api.post('/import', { source_path: sourcePath });
    return response.data;
  },

  getStatus: async (): Promise<ImportStatus> => {
    const response = await api.get('/import/status');
    return response.data;
  },
};

export const getPosterProxyUrl = (doubanId: string): string => {
  return `${API_URL}/movies/${doubanId}/poster`;
};

export default api;
