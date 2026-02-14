import { create } from 'zustand';

export interface FilterState {
  type: 'movie' | 'tv' | null;
  minRating: number;
  maxRating: number;
  minRatingCount: number;
  minYear: number | null;
  maxYear: number | null;
  selectedGenres: string[];
  excludedGenres: string[];
  searchQuery: string;
  sortBy: 'rating' | 'rating_count' | 'year';
  sortOrder: 'asc' | 'desc';

  // Actions
  setType: (type: 'movie' | 'tv' | null) => void;
  setMinRating: (rating: number) => void;
  setMaxRating: (rating: number) => void;
  setMinRatingCount: (count: number) => void;
  setMinYear: (year: number | null) => void;
  setMaxYear: (year: number | null) => void;
  toggleGenre: (genre: string) => void;
  setSelectedGenres: (genres: string[]) => void;
  clearGenres: () => void;
  toggleExcludedGenre: (genre: string) => void;
  setExcludedGenres: (genres: string[]) => void;
  clearExcludedGenres: () => void;
  cycleGenre: (genre: string) => void;
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
  minYear: null as number | null,
  maxYear: null as number | null,
  selectedGenres: [] as string[],
  excludedGenres: [] as string[],
  searchQuery: '',
  sortBy: 'rating' as const,
  sortOrder: 'desc' as const,
};

export const useFilterStore = create<FilterState>()((set) => ({
  ...initialState,

  setType: (type) => set({ type }),

  setMinRating: (minRating) => set({ minRating }),

  setMaxRating: (maxRating) => set({ maxRating }),

  setMinRatingCount: (minRatingCount) => set({ minRatingCount }),

  setMinYear: (minYear) => set({ minYear }),

  setMaxYear: (maxYear) => set({ maxYear }),

  toggleGenre: (genre) =>
    set((state) => ({
      selectedGenres: state.selectedGenres.includes(genre)
        ? state.selectedGenres.filter((g) => g !== genre)
        : [...state.selectedGenres, genre],
      // If a genre is selected, it cannot be excluded
      excludedGenres: state.excludedGenres.filter((g) => g !== genre),
    })),

  setSelectedGenres: (selectedGenres) => set({ selectedGenres }),

  clearGenres: () => set({ selectedGenres: [] }),

  toggleExcludedGenre: (genre) =>
    set((state) => ({
      excludedGenres: state.excludedGenres.includes(genre)
        ? state.excludedGenres.filter((g) => g !== genre)
        : [...state.excludedGenres, genre],
      // If a genre is excluded, it cannot be selected (inclusive)
      selectedGenres: state.selectedGenres.filter((g) => g !== genre),
    })),

  setExcludedGenres: (excludedGenres) => set({ excludedGenres }),

  clearExcludedGenres: () => set({ excludedGenres: [] }),

  cycleGenre: (genre) =>
    set((state) => {
      if (state.selectedGenres.includes(genre)) {
        // Included -> Excluded
        return {
          selectedGenres: state.selectedGenres.filter((g) => g !== genre),
          excludedGenres: [...state.excludedGenres, genre],
        };
      } else if (state.excludedGenres.includes(genre)) {
        // Excluded -> Unselected
        return {
          excludedGenres: state.excludedGenres.filter((g) => g !== genre),
        };
      } else {
        // Unselected -> Included
        return {
          selectedGenres: [...state.selectedGenres, genre],
          excludedGenres: state.excludedGenres.filter((g) => g !== genre),
        };
      }
    }),

  setSearchQuery: (searchQuery) => set({ searchQuery }),

  setSortBy: (sortBy) => set({ sortBy }),

  setSortOrder: (sortOrder) => set({ sortOrder }),

  resetFilters: () => set(initialState),
}));
