import { useEffect, useRef, useCallback } from 'react';
import { useFilterStore, type FilterState } from '../store/useFilterStore';

export function useUrlSync() {
  const { committedFilters, setCommittedFilters } = useFilterStore();

  const isInitialLoad = useRef(true);

  // Function to sync URL params to store
  const syncUrlToStore = useCallback(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.toString() === '') return; // Don't override if URL is empty

    const filters: Partial<FilterState> = {};

    if (params.has('type')) {
      const val = params.get('type');
      filters.type = val === 'movie' || val === 'tv' ? val : null;
    }
    if (params.has('minRating')) filters.minRating = Number(params.get('minRating'));
    if (params.has('maxRating')) filters.maxRating = Number(params.get('maxRating'));
    if (params.has('minRatingCount')) filters.minRatingCount = Number(params.get('minRatingCount'));
    if (params.has('minYear')) filters.minYear = Number(params.get('minYear'));
    if (params.has('maxYear')) filters.maxYear = Number(params.get('maxYear'));
    if (params.has('searchQuery')) filters.searchQuery = params.get('searchQuery') || '';
    if (params.has('sortBy')) {
      const val = params.get('sortBy');
      if (val === 'rating' || val === 'rating_count' || val === 'year') filters.sortBy = val;
    }
    if (params.has('sortOrder')) {
      const val = params.get('sortOrder');
      if (val === 'asc' || val === 'desc') filters.sortOrder = val;
    }
    if (params.has('selectedGenres')) {
      filters.selectedGenres = params.get('selectedGenres')?.split(',').filter(Boolean) || [];
    }
    if (params.has('excludedGenres')) {
      filters.excludedGenres = params.get('excludedGenres')?.split(',').filter(Boolean) || [];
    }
    if (params.has('selectedRegions')) {
      filters.selectedRegions = params.get('selectedRegions')?.split(',').filter(Boolean) || [];
    }

    // Use setCommittedFilters to batch update and avoid intermediate API calls
    if (Object.keys(filters).length > 0) {
      setCommittedFilters(filters);
    }
  }, [setCommittedFilters]);

  // Initial load
  useEffect(() => {
    syncUrlToStore();
    isInitialLoad.current = false;
  }, [syncUrlToStore]);

  // Handle browser back/forward
  useEffect(() => {
    const handlePopState = () => {
      syncUrlToStore();
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [syncUrlToStore]);

  // Store -> URL (sync only committedFilters to avoid URL jitter)
  useEffect(() => {
    if (isInitialLoad.current) return;

    const {
      type,
      minRating,
      maxRating,
      minRatingCount,
      minYear,
      maxYear,
      selectedGenres,
      excludedGenres,
      selectedRegions,
      searchQuery,
      sortBy,
      sortOrder,
    } = committedFilters;

    const params = new URLSearchParams();
    if (type) params.set('type', type);
    if (minRating > 0) params.set('minRating', minRating.toString());
    if (maxRating < 10) params.set('maxRating', maxRating.toString());
    if (minRatingCount > 0) params.set('minRatingCount', minRatingCount.toString());
    if (minYear !== null) params.set('minYear', minYear.toString());
    if (maxYear !== null) params.set('maxYear', maxYear.toString());
    if (selectedGenres.length > 0) params.set('selectedGenres', selectedGenres.join(','));
    if (excludedGenres.length > 0) params.set('excludedGenres', excludedGenres.join(','));
    if (selectedRegions.length > 0) params.set('selectedRegions', selectedRegions.join(','));
    if (searchQuery) params.set('searchQuery', searchQuery);
    if (sortBy !== 'rating_count') params.set('sortBy', sortBy);
    if (sortOrder !== 'desc') params.set('sortOrder', sortOrder);

    const newSearch = params.toString();
    const currentSearch = window.location.search.replace(/^\?/, '');

    if (newSearch !== currentSearch) {
      const newUrl = `${window.location.pathname}${newSearch ? '?' + newSearch : ''}`;
      window.history.replaceState(null, '', newUrl);
    }
  }, [committedFilters]);
}
