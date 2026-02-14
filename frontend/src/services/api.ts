import axios from 'axios';
import type { MoviesListResponse, GenreCount, StatsResponse } from '../types/movie';
import { useNotificationStore } from '../store/useNotificationStore';

const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for global error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 429) {
      useNotificationStore.getState().addNotification('操作太频繁，请稍后再试', 'warning');
    }
    return Promise.reject(error);
  },
);

export interface MoviesParams {
  cursor?: string;
  limit?: number;
  type?: 'movie' | 'tv';
  min_rating?: number;
  max_rating?: number;
  min_rating_count?: number;
  min_year?: number;
  max_year?: number;
  genres?: string[];
  exclude_genres?: string[];
  search?: string;
  sort_by?: 'rating' | 'rating_count' | 'year';
  sort_order?: 'asc' | 'desc';
}

export const moviesApi = {
  getMovies: async (params: MoviesParams = {}): Promise<MoviesListResponse> => {
    const response = await api.get('/movies', {
      params: {
        ...params,
        genres: params.genres?.join(','),
        exclude_genres: params.exclude_genres?.join(','),
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

export const getPosterProxyUrl = (id: number): string => {
  return `${API_URL}/movies/${id}/poster`;
};

export default api;
