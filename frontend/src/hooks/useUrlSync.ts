import { useEffect, useRef, useCallback } from 'react';
import { useFilterStore } from '../store/useFilterStore';
import { parseUrlParams } from '../utils/urlParams';

export function useUrlSync() {
  const { committedFilters, setCommittedFilters } = useFilterStore();

  const isInitialLoad = useRef(true);

  // Function to sync URL params to store
  const syncUrlToStore = useCallback(() => {
    const filters = parseUrlParams();
    if (Object.keys(filters).length === 0) return; // Don't override if URL is empty

    // Use setCommittedFilters to batch update and avoid intermediate API calls
    setCommittedFilters(filters);
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
