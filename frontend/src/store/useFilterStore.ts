import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface FilterState {
  type: 'movie' | 'tv' | null;
  minRating: number;
  maxRating: number;
  minRatingCount: number;
  selectedGenres: string[];
  searchQuery: string;
  sortBy: 'rating' | 'rating_count' | 'year';
  sortOrder: 'asc' | 'desc';
  
  // Actions
  setType: (type: 'movie' | 'tv' | null) => void;
  setMinRating: (rating: number) => void;
  setMaxRating: (rating: number) => void;
  setMinRatingCount: (count: number) => void;
  toggleGenre: (genre: string) => void;
  clearGenres: () => void;
  setSearchQuery: (query: string) => void;
  setSortBy: (sortBy: 'rating' | 'rating_count' | 'year') => void;
  setSortOrder: (order: 'asc' | 'desc') => void;
  resetFilters: () => void;
}

const initialState = {
  type: null as 'movie' | 'tv' | null,
  minRating: 0,
  maxRating: 10,
  minRatingCount: 0,
  selectedGenres: [] as string[],
  searchQuery: '',
  sortBy: 'rating' as const,
  sortOrder: 'desc' as const,
};

export const useFilterStore = create<FilterState>()(
  persist(
    (set) => ({
      ...initialState,
      
      setType: (type) => set({ type }),
      
      setMinRating: (minRating) => set({ minRating }),
      
      setMaxRating: (maxRating) => set({ maxRating }),
      
      setMinRatingCount: (minRatingCount) => set({ minRatingCount }),
      
      toggleGenre: (genre) => set((state) => ({
        selectedGenres: state.selectedGenres.includes(genre)
          ? state.selectedGenres.filter((g) => g !== genre)
          : [...state.selectedGenres, genre],
      })),
      
      clearGenres: () => set({ selectedGenres: [] }),
      
      setSearchQuery: (searchQuery) => set({ searchQuery }),
      
      setSortBy: (sortBy) => set({ sortBy }),
      
      setSortOrder: (sortOrder) => set({ sortOrder }),
      
      resetFilters: () => set(initialState),
    }),
    {
      name: 'douban-filters',
    }
  )
);
