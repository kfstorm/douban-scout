import { create } from 'zustand';
import { parseUrlParams } from '../utils/urlParams';

export interface FilterState {
  type: 'movie' | 'tv' | null;
  minRating: number;
  maxRating: number;
  minRatingCount: number;
  minYear: number | null;
  maxYear: number | null;
  selectedGenres: string[];
  excludedGenres: string[];
  selectedRegions: string[];
  searchQuery: string;
  sortBy: 'rating' | 'rating_count' | 'year';
  sortOrder: 'asc' | 'desc';
}

export interface FilterStore extends FilterState {
  // Committed filters (debounced, triggers API calls)
  committedFilters: FilterState;

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
  toggleRegion: (region: string) => void;
  setSelectedRegions: (regions: string[]) => void;
  clearRegions: () => void;
  setSearchQuery: (query: string) => void;
  setSortBy: (sortBy: 'rating' | 'rating_count' | 'year') => void;
  setSortOrder: (order: 'asc' | 'desc') => void;
  resetFilters: () => void;
  // Batch update committed filters (for initial load)
  setCommittedFilters: (filters: Partial<FilterState>) => void;
  // Get all filters as an object
  getFilters: () => FilterState;
}

const DEBOUNCE_DELAY = 1000; // ms

// Parse URL params synchronously during store initialization
const urlFilters = parseUrlParams();

const initialState: FilterState = {
  type: null,
  minRating: 0,
  maxRating: 10,
  minRatingCount: 0,
  minYear: null,
  maxYear: null,
  selectedGenres: [],
  excludedGenres: [],
  selectedRegions: [],
  searchQuery: '',
  sortBy: 'rating_count',
  sortOrder: 'desc',
  ...urlFilters, // Apply URL params to initial state
};

// Debounce helper
const debounce = <T extends (...args: unknown[]) => void>(fn: T, delay: number) => {
  let timeoutId: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
};

export const useFilterStore = create<FilterStore>()((set, get) => {
  // Debounced commit function
  const commitFilters = debounce(() => {
    const state = get();
    set({
      committedFilters: {
        type: state.type,
        minRating: state.minRating,
        maxRating: state.maxRating,
        minRatingCount: state.minRatingCount,
        minYear: state.minYear,
        maxYear: state.maxYear,
        selectedGenres: state.selectedGenres,
        excludedGenres: state.excludedGenres,
        selectedRegions: state.selectedRegions,
        searchQuery: state.searchQuery,
        sortBy: state.sortBy,
        sortOrder: state.sortOrder,
      },
    });
  }, DEBOUNCE_DELAY);

  return {
    ...initialState,
    committedFilters: initialState, // Both states start with URL params applied

    setType: (type: 'movie' | 'tv' | null) => {
      set({ type });
      commitFilters();
    },

    setMinRating: (minRating: number) => {
      set({ minRating });
      commitFilters();
    },

    setMaxRating: (maxRating: number) => {
      set({ maxRating });
      commitFilters();
    },

    setMinRatingCount: (minRatingCount: number) => {
      set({ minRatingCount });
      commitFilters();
    },

    setMinYear: (minYear: number | null) => {
      set({ minYear });
      commitFilters();
    },

    setMaxYear: (maxYear: number | null) => {
      set({ maxYear });
      commitFilters();
    },

    toggleGenre: (genre: string) => {
      set((state) => ({
        selectedGenres: state.selectedGenres.includes(genre)
          ? state.selectedGenres.filter((g) => g !== genre)
          : [...state.selectedGenres, genre],
        excludedGenres: state.excludedGenres.filter((g) => g !== genre),
      }));
      commitFilters();
    },

    setSelectedGenres: (selectedGenres: string[]) => {
      set({ selectedGenres });
      commitFilters();
    },

    clearGenres: () => {
      set({ selectedGenres: [] });
      commitFilters();
    },

    toggleExcludedGenre: (genre: string) => {
      set((state) => ({
        excludedGenres: state.excludedGenres.includes(genre)
          ? state.excludedGenres.filter((g) => g !== genre)
          : [...state.excludedGenres, genre],
        selectedGenres: state.selectedGenres.filter((g) => g !== genre),
      }));
      commitFilters();
    },

    setExcludedGenres: (excludedGenres: string[]) => {
      set({ excludedGenres });
      commitFilters();
    },

    clearExcludedGenres: () => {
      set({ excludedGenres: [] });
      commitFilters();
    },

    cycleGenre: (genre: string) => {
      set((state) => {
        if (state.selectedGenres.includes(genre)) {
          return {
            selectedGenres: state.selectedGenres.filter((g) => g !== genre),
            excludedGenres: [...state.excludedGenres, genre],
          };
        } else if (state.excludedGenres.includes(genre)) {
          return {
            excludedGenres: state.excludedGenres.filter((g) => g !== genre),
          };
        } else {
          return {
            selectedGenres: [...state.selectedGenres, genre],
            excludedGenres: state.excludedGenres.filter((g) => g !== genre),
          };
        }
      });
      commitFilters();
    },

    toggleRegion: (region: string) => {
      set((state) => ({
        selectedRegions: state.selectedRegions.includes(region)
          ? state.selectedRegions.filter((r) => r !== region)
          : [...state.selectedRegions, region],
      }));
      commitFilters();
    },

    setSelectedRegions: (selectedRegions: string[]) => {
      set({ selectedRegions });
      commitFilters();
    },

    clearRegions: () => {
      set({ selectedRegions: [] });
      commitFilters();
    },

    setSearchQuery: (searchQuery: string) => {
      set({ searchQuery });
      commitFilters();
    },

    setSortBy: (sortBy: 'rating' | 'rating_count' | 'year') => {
      set({ sortBy });
      commitFilters();
    },

    setSortOrder: (sortOrder: 'asc' | 'desc') => {
      set({ sortOrder });
      commitFilters();
    },

    resetFilters: () => {
      set(initialState);
      commitFilters();
    },

    setCommittedFilters: (filters: Partial<FilterState>) => {
      const newState = { ...initialState, ...filters };
      set({
        ...newState,
        committedFilters: newState,
      });
    },

    getFilters: () => {
      const state = get();
      return {
        type: state.type,
        minRating: state.minRating,
        maxRating: state.maxRating,
        minRatingCount: state.minRatingCount,
        minYear: state.minYear,
        maxYear: state.maxYear,
        selectedGenres: state.selectedGenres,
        excludedGenres: state.excludedGenres,
        selectedRegions: state.selectedRegions,
        searchQuery: state.searchQuery,
        sortBy: state.sortBy,
        sortOrder: state.sortOrder,
      };
    },
  };
});
