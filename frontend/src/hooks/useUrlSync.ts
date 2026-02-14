import { useEffect, useRef, useCallback } from 'react';
import { useFilterStore } from '../store/useFilterStore';

export function useUrlSync() {
  const {
    type,
    minRating,
    maxRating,
    minRatingCount,
    minYear,
    maxYear,
    selectedGenres,
    excludedGenres,
    searchQuery,
    sortBy,
    sortOrder,
    setType,
    setMinRating,
    setMaxRating,
    setMinRatingCount,
    setMinYear,
    setMaxYear,
    setSearchQuery,
    setSortBy,
    setSortOrder,
    setSelectedGenres,
    setExcludedGenres,
  } = useFilterStore();

  const isInitialLoad = useRef(true);

  // Function to sync URL params to store
  const syncUrlToStore = useCallback(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.toString() === '') return; // Don't override if URL is empty (keep localStorage)

    if (params.has('type')) {
      const val = params.get('type');
      setType(val === 'movie' || val === 'tv' ? val : null);
    }
    if (params.has('min_rating')) setMinRating(Number(params.get('min_rating')));
    if (params.has('max_rating')) setMaxRating(Number(params.get('max_rating')));
    if (params.has('min_rating_count')) setMinRatingCount(Number(params.get('min_rating_count')));
    if (params.has('min_year')) setMinYear(Number(params.get('min_year')));
    if (params.has('max_year')) setMaxYear(Number(params.get('max_year')));
    if (params.has('q')) setSearchQuery(params.get('q') || '');
    if (params.has('sort_by')) {
      const val = params.get('sort_by');
      if (val === 'rating' || val === 'rating_count' || val === 'year') setSortBy(val);
    }
    if (params.has('sort_order')) {
      const val = params.get('sort_order');
      if (val === 'asc' || val === 'desc') setSortOrder(val);
    }

    if (params.has('genres')) {
      const selected = params.get('genres')?.split(',').filter(Boolean) || [];
      setSelectedGenres(selected);
    }
    if (params.has('exclude_genres')) {
      const excluded = params.get('exclude_genres')?.split(',').filter(Boolean) || [];
      setExcludedGenres(excluded);
    }
  }, [
    setType,
    setMinRating,
    setMaxRating,
    setMinRatingCount,
    setSearchQuery,
    setSortBy,
    setSortOrder,
    setSelectedGenres,
    setExcludedGenres,
    setMinYear,
    setMaxYear,
  ]);

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

  // Store -> URL
  useEffect(() => {
    if (isInitialLoad.current) return;

    const params = new URLSearchParams();
    if (type) params.set('type', type);
    if (minRating > 0) params.set('min_rating', minRating.toString());
    if (maxRating < 10) params.set('max_rating', maxRating.toString());
    if (minRatingCount > 0) params.set('min_rating_count', minRatingCount.toString());
    if (minYear !== null) params.set('min_year', minYear.toString());
    if (maxYear !== null) params.set('max_year', maxYear.toString());
    if (selectedGenres.length > 0) params.set('genres', selectedGenres.join(','));
    if (excludedGenres.length > 0) params.set('exclude_genres', excludedGenres.join(','));
    if (searchQuery) params.set('q', searchQuery);
    if (sortBy !== 'rating') params.set('sort_by', sortBy);
    if (sortOrder !== 'desc') params.set('sort_order', sortOrder);

    const newSearch = params.toString();
    const currentSearch = window.location.search.replace(/^\?/, '');

    if (newSearch !== currentSearch) {
      const newUrl = `${window.location.pathname}${newSearch ? '?' + newSearch : ''}`;
      window.history.replaceState(null, '', newUrl);
    }
  }, [
    type,
    minRating,
    maxRating,
    minRatingCount,
    minYear,
    maxYear,
    selectedGenres,
    excludedGenres,
    searchQuery,
    sortBy,
    sortOrder,
  ]);
}
