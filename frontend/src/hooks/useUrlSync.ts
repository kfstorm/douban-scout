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
    selectedRegions,
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
    setSelectedRegions,
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
    if (params.has('minRating')) setMinRating(Number(params.get('minRating')));
    if (params.has('maxRating')) setMaxRating(Number(params.get('maxRating')));
    if (params.has('minRatingCount')) setMinRatingCount(Number(params.get('minRatingCount')));
    if (params.has('minYear')) setMinYear(Number(params.get('minYear')));
    if (params.has('maxYear')) setMaxYear(Number(params.get('maxYear')));
    if (params.has('searchQuery')) setSearchQuery(params.get('searchQuery') || '');
    if (params.has('sortBy')) {
      const val = params.get('sortBy');
      if (val === 'rating' || val === 'rating_count' || val === 'year') setSortBy(val);
    }
    if (params.has('sortOrder')) {
      const val = params.get('sortOrder');
      if (val === 'asc' || val === 'desc') setSortOrder(val);
    }

    if (params.has('selectedGenres')) {
      const selected = params.get('selectedGenres')?.split(',').filter(Boolean) || [];
      setSelectedGenres(selected);
    }
    if (params.has('excludedGenres')) {
      const excluded = params.get('excludedGenres')?.split(',').filter(Boolean) || [];
      setExcludedGenres(excluded);
    }
    if (params.has('selectedRegions')) {
      const selected = params.get('selectedRegions')?.split(',').filter(Boolean) || [];
      setSelectedRegions(selected);
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
    setSelectedRegions,
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
  }, [
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
  ]);
}
