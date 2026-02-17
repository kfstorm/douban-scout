import type { FilterState } from '../store/useFilterStore';

export function parseUrlParams(): Partial<FilterState> {
  if (typeof window === 'undefined') return {};

  const params = new URLSearchParams(window.location.search);
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

  return filters;
}
