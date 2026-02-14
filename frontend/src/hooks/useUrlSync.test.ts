import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useUrlSync } from './useUrlSync';
import { useFilterStore } from '../store/useFilterStore';

describe('useUrlSync', () => {
  const originalLocation = window.location;
  let mockLocation: Location;

  beforeEach(() => {
    useFilterStore.setState({
      type: null,
      minRating: 0,
      maxRating: 10,
      minRatingCount: 0,
      minYear: null,
      maxYear: null,
      selectedGenres: [],
      excludedGenres: [],
      searchQuery: '',
      sortBy: 'rating',
      sortOrder: 'desc',
    });

    mockLocation = {
      ...originalLocation,
      search: '',
      pathname: '/',
    } as Location;

    Object.defineProperty(window, 'location', {
      writable: true,
      value: mockLocation,
    });

    window.history.replaceState = vi.fn();
    window.addEventListener = vi.fn();
    window.removeEventListener = vi.fn();
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      writable: true,
      value: originalLocation,
    });
  });

  describe('URL to Store Sync', () => {
    it('should sync type from URL', () => {
      mockLocation.search = '?type=movie';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().type).toBe('movie');
    });

    it('should sync tv type from URL', () => {
      mockLocation.search = '?type=tv';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().type).toBe('tv');
    });

    it('should set type to null for invalid value', () => {
      mockLocation.search = '?type=invalid';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().type).toBeNull();
    });

    it('should sync min_rating from URL', () => {
      mockLocation.search = '?min_rating=7';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().minRating).toBe(7);
    });

    it('should sync max_rating from URL', () => {
      mockLocation.search = '?max_rating=9';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().maxRating).toBe(9);
    });

    it('should sync min_rating_count from URL', () => {
      mockLocation.search = '?min_rating_count=1000';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().minRatingCount).toBe(1000);
    });

    it('should sync min_year from URL', () => {
      mockLocation.search = '?min_year=2000';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().minYear).toBe(2000);
    });

    it('should sync max_year from URL', () => {
      mockLocation.search = '?max_year=2023';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().maxYear).toBe(2023);
    });

    it('should sync search query from URL', () => {
      mockLocation.search = '?q=测试';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().searchQuery).toBe('测试');
    });

    it('should sync sort_by from URL', () => {
      mockLocation.search = '?sort_by=year';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().sortBy).toBe('year');
    });

    it('should sync sort_order from URL', () => {
      mockLocation.search = '?sort_order=asc';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().sortOrder).toBe('asc');
    });

    it('should sync genres from URL', () => {
      mockLocation.search = '?genres=动作,喜剧';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().selectedGenres).toEqual(['动作', '喜剧']);
    });

    it('should sync exclude_genres from URL', () => {
      mockLocation.search = '?exclude_genres=恐怖,惊悚';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().excludedGenres).toEqual(['恐怖', '惊悚']);
    });

    it('should not override store if URL is empty', () => {
      useFilterStore.getState().setType('movie');
      useFilterStore.getState().setMinRating(8);

      mockLocation.search = '';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().type).toBe('movie');
      expect(useFilterStore.getState().minRating).toBe(8);
    });
  });

  describe('Popstate Event', () => {
    it('should add popstate listener on mount', () => {
      renderHook(() => useUrlSync());

      expect(window.addEventListener).toHaveBeenCalledWith('popstate', expect.any(Function));
    });

    it('should remove popstate listener on unmount', () => {
      const { unmount } = renderHook(() => useUrlSync());
      unmount();

      expect(window.removeEventListener).toHaveBeenCalledWith('popstate', expect.any(Function));
    });
  });

  describe('Invalid Sort Values', () => {
    it('should not set invalid sort_by value', () => {
      mockLocation.search = '?sort_by=invalid';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().sortBy).toBe('rating');
    });

    it('should not set invalid sort_order value', () => {
      mockLocation.search = '?sort_order=invalid';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().sortOrder).toBe('desc');
    });
  });
});
