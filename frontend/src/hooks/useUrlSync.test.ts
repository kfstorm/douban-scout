import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
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
      selectedRegions: [],
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

    it('should sync minRating from URL', () => {
      mockLocation.search = '?minRating=7';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().minRating).toBe(7);
    });

    it('should sync maxRating from URL', () => {
      mockLocation.search = '?maxRating=9';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().maxRating).toBe(9);
    });

    it('should sync minRatingCount from URL', () => {
      mockLocation.search = '?minRatingCount=1000';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().minRatingCount).toBe(1000);
    });

    it('should sync minYear from URL', () => {
      mockLocation.search = '?minYear=2000';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().minYear).toBe(2000);
    });

    it('should sync maxYear from URL', () => {
      mockLocation.search = '?maxYear=2023';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().maxYear).toBe(2023);
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

  describe('Generic Sync Coverage (Exact Match)', () => {
    const getParamName = (key: string) => key;

    const testValues: Record<string, string | string[] | number | null> = {
      type: 'tv',
      minRating: 8,
      maxRating: 9,
      minRatingCount: 500,
      minYear: 1990,
      maxYear: 2010,
      selectedGenres: ['动作'],
      excludedGenres: ['喜剧'],
      selectedRegions: ['中国'],
      searchQuery: 'test',
      sortBy: 'year',
      sortOrder: 'asc',
    };

    const state = useFilterStore.getState();
    const stateKeys = Object.keys(state).filter(
      (key) => typeof (state as unknown as Record<string, unknown>)[key] !== 'function',
    );

    stateKeys.forEach((storeKey) => {
      const param = getParamName(storeKey);
      const value = testValues[storeKey];

      it(`should sync ${storeKey} from URL to Store (param: ${param})`, () => {
        if (value === undefined) {
          throw new Error(
            `No test value defined for filter '${storeKey}'. Please add it to 'testValues' in the test file.`,
          );
        }

        const urlValue = Array.isArray(value) ? value.join(',') : String(value);
        mockLocation.search = `?${param}=${encodeURIComponent(urlValue)}`;
        renderHook(() => useUrlSync());

        const currentState = useFilterStore.getState() as unknown as Record<string, unknown>;
        expect(
          currentState[storeKey],
          `Filter '${storeKey}' was not correctly synchronized from URL parameter '${param}' to the Store. Check 'syncUrlToStore' in useUrlSync.ts.`,
        ).toEqual(value);
      });

      it(`should sync ${storeKey} from Store to URL (param: ${param})`, () => {
        renderHook(() => useUrlSync());

        const currentState = useFilterStore.getState() as unknown as Record<string, unknown>;
        const actionName = `set${storeKey.charAt(0).toUpperCase()}${storeKey.slice(1)}`;

        // Special cases for action names if they don't follow the pattern
        let action = currentState[actionName];
        if (storeKey === 'selectedGenres') action = currentState.setSelectedGenres;
        if (storeKey === 'excludedGenres') action = currentState.setExcludedGenres;
        if (storeKey === 'selectedRegions') action = currentState.setSelectedRegions;

        if (typeof action !== 'function') {
          throw new Error(
            `Action '${actionName}' not found for key '${storeKey}'. Ensure the store provides a setter following the naming convention.`,
          );
        }

        act(() => {
          (action as (v: unknown) => void)(value);
        });

        const urlValue = Array.isArray(value) ? value.join(',') : String(value);
        expect(
          window.history.replaceState,
          `Changing filter '${storeKey}' in the Store did not update the URL parameter '${param}'. Check the dependency array and logic in the 'Store -> URL' useEffect in useUrlSync.ts.`,
        ).toHaveBeenCalledWith(
          null,
          '',
          expect.stringContaining(`${param}=${encodeURIComponent(urlValue)}`),
        );
      });
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
    it('should not set invalid sortBy value', () => {
      mockLocation.search = '?sortBy=invalid';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().sortBy).toBe('rating');
    });

    it('should not set invalid sortOrder value', () => {
      mockLocation.search = '?sortOrder=invalid';
      renderHook(() => useUrlSync());

      expect(useFilterStore.getState().sortOrder).toBe('desc');
    });
  });
});
