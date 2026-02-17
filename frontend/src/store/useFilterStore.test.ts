import { describe, it, expect, beforeEach } from 'vitest';
import { useFilterStore, defaultFilters } from './useFilterStore';

describe('useFilterStore', () => {
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
      sortBy: 'rating_count',
      sortOrder: 'desc',
    });
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useFilterStore.getState();
      expect(state.type).toBeNull();
      expect(state.minRating).toBe(0);
      expect(state.maxRating).toBe(10);
      expect(state.minRatingCount).toBe(0);
      expect(state.minYear).toBeNull();
      expect(state.maxYear).toBeNull();
      expect(state.selectedGenres).toEqual([]);
      expect(state.excludedGenres).toEqual([]);
      expect(state.selectedRegions).toEqual([]);
      expect(state.searchQuery).toBe('');
      expect(state.sortBy).toBe('rating_count');
      expect(state.sortOrder).toBe('desc');
    });
  });

  describe('Type', () => {
    it('should set type to movie', () => {
      useFilterStore.getState().setType('movie');
      expect(useFilterStore.getState().type).toBe('movie');
    });

    it('should set type to tv', () => {
      useFilterStore.getState().setType('tv');
      expect(useFilterStore.getState().type).toBe('tv');
    });

    it('should set type to null', () => {
      useFilterStore.getState().setType('movie');
      useFilterStore.getState().setType(null);
      expect(useFilterStore.getState().type).toBeNull();
    });
  });

  describe('Rating', () => {
    it('should set minimum rating', () => {
      useFilterStore.getState().setMinRating(7);
      expect(useFilterStore.getState().minRating).toBe(7);
    });

    it('should set maximum rating', () => {
      useFilterStore.getState().setMaxRating(9);
      expect(useFilterStore.getState().maxRating).toBe(9);
    });
  });

  describe('Rating Count', () => {
    it('should set minimum rating count', () => {
      useFilterStore.getState().setMinRatingCount(1000);
      expect(useFilterStore.getState().minRatingCount).toBe(1000);
    });
  });

  describe('Year', () => {
    it('should set minimum year', () => {
      useFilterStore.getState().setMinYear(2000);
      expect(useFilterStore.getState().minYear).toBe(2000);
    });

    it('should set maximum year', () => {
      useFilterStore.getState().setMaxYear(2023);
      expect(useFilterStore.getState().maxYear).toBe(2023);
    });

    it('should set year to null', () => {
      useFilterStore.getState().setMinYear(2000);
      useFilterStore.getState().setMinYear(null);
      expect(useFilterStore.getState().minYear).toBeNull();
    });
  });

  describe('Genre Management', () => {
    describe('toggleGenre', () => {
      it('should add genre to selected genres', () => {
        useFilterStore.getState().toggleGenre('动作');
        expect(useFilterStore.getState().selectedGenres).toContain('动作');
      });

      it('should remove genre from selected genres if already selected', () => {
        useFilterStore.getState().toggleGenre('动作');
        useFilterStore.getState().toggleGenre('动作');
        expect(useFilterStore.getState().selectedGenres).not.toContain('动作');
      });

      it('should remove genre from excluded genres when selecting', () => {
        useFilterStore.getState().toggleExcludedGenre('动作');
        useFilterStore.getState().toggleGenre('动作');
        expect(useFilterStore.getState().excludedGenres).not.toContain('动作');
        expect(useFilterStore.getState().selectedGenres).toContain('动作');
      });
    });

    describe('setSelectedGenres', () => {
      it('should set selected genres array', () => {
        useFilterStore.getState().setSelectedGenres(['动作', '喜剧']);
        expect(useFilterStore.getState().selectedGenres).toEqual(['动作', '喜剧']);
      });
    });

    describe('clearGenres', () => {
      it('should clear all selected genres', () => {
        useFilterStore.getState().setSelectedGenres(['动作', '喜剧']);
        useFilterStore.getState().clearGenres();
        expect(useFilterStore.getState().selectedGenres).toEqual([]);
      });
    });

    describe('toggleExcludedGenre', () => {
      it('should add genre to excluded genres', () => {
        useFilterStore.getState().toggleExcludedGenre('恐怖');
        expect(useFilterStore.getState().excludedGenres).toContain('恐怖');
      });

      it('should remove genre from excluded genres if already excluded', () => {
        useFilterStore.getState().toggleExcludedGenre('恐怖');
        useFilterStore.getState().toggleExcludedGenre('恐怖');
        expect(useFilterStore.getState().excludedGenres).not.toContain('恐怖');
      });

      it('should remove genre from selected genres when excluding', () => {
        useFilterStore.getState().toggleGenre('动作');
        useFilterStore.getState().toggleExcludedGenre('动作');
        expect(useFilterStore.getState().selectedGenres).not.toContain('动作');
        expect(useFilterStore.getState().excludedGenres).toContain('动作');
      });
    });

    describe('setExcludedGenres', () => {
      it('should set excluded genres array', () => {
        useFilterStore.getState().setExcludedGenres(['恐怖', '惊悚']);
        expect(useFilterStore.getState().excludedGenres).toEqual(['恐怖', '惊悚']);
      });
    });

    describe('clearExcludedGenres', () => {
      it('should clear all excluded genres', () => {
        useFilterStore.getState().setExcludedGenres(['恐怖', '惊悚']);
        useFilterStore.getState().clearExcludedGenres();
        expect(useFilterStore.getState().excludedGenres).toEqual([]);
      });
    });

    describe('cycleGenre', () => {
      it('should transition from unselected to selected', () => {
        useFilterStore.getState().cycleGenre('动作');
        expect(useFilterStore.getState().selectedGenres).toContain('动作');
        expect(useFilterStore.getState().excludedGenres).not.toContain('动作');
      });

      it('should transition from selected to excluded', () => {
        useFilterStore.getState().cycleGenre('动作');
        useFilterStore.getState().cycleGenre('动作');
        expect(useFilterStore.getState().selectedGenres).not.toContain('动作');
        expect(useFilterStore.getState().excludedGenres).toContain('动作');
      });

      it('should transition from excluded to unselected', () => {
        useFilterStore.getState().cycleGenre('动作');
        useFilterStore.getState().cycleGenre('动作');
        useFilterStore.getState().cycleGenre('动作');
        expect(useFilterStore.getState().selectedGenres).not.toContain('动作');
        expect(useFilterStore.getState().excludedGenres).not.toContain('动作');
      });
    });
  });

  describe('Region Management', () => {
    describe('toggleRegion', () => {
      it('should add region to selected regions', () => {
        useFilterStore.getState().toggleRegion('中国大陆');
        expect(useFilterStore.getState().selectedRegions).toContain('中国大陆');
      });

      it('should remove region from selected regions if already selected', () => {
        useFilterStore.getState().toggleRegion('中国大陆');
        useFilterStore.getState().toggleRegion('中国大陆');
        expect(useFilterStore.getState().selectedRegions).not.toContain('中国大陆');
      });
    });

    describe('setSelectedRegions', () => {
      it('should set selected regions array', () => {
        useFilterStore.getState().setSelectedRegions(['美国', '日本']);
        expect(useFilterStore.getState().selectedRegions).toEqual(['美国', '日本']);
      });
    });

    describe('clearRegions', () => {
      it('should clear all selected regions', () => {
        useFilterStore.getState().setSelectedRegions(['美国', '日本']);
        useFilterStore.getState().clearRegions();
        expect(useFilterStore.getState().selectedRegions).toEqual([]);
      });
    });
  });

  describe('Search', () => {
    it('should set search query', () => {
      useFilterStore.getState().setSearchQuery('测试');
      expect(useFilterStore.getState().searchQuery).toBe('测试');
    });

    it('should clear search query', () => {
      useFilterStore.getState().setSearchQuery('测试');
      useFilterStore.getState().setSearchQuery('');
      expect(useFilterStore.getState().searchQuery).toBe('');
    });
  });

  describe('Sorting', () => {
    it('should set sort by field', () => {
      useFilterStore.getState().setSortBy('year');
      expect(useFilterStore.getState().sortBy).toBe('year');
    });

    it('should set sort order', () => {
      useFilterStore.getState().setSortOrder('asc');
      expect(useFilterStore.getState().sortOrder).toBe('asc');
    });
  });

  describe('Reset', () => {
    it('should reset all filters to initial state', () => {
      useFilterStore.getState().setType('movie');
      useFilterStore.getState().setMinRating(8);
      useFilterStore.getState().setMaxRating(9);
      useFilterStore.getState().setMinRatingCount(1000);
      useFilterStore.getState().setMinYear(2000);
      useFilterStore.getState().setMaxYear(2023);
      useFilterStore.getState().setSelectedGenres(['动作']);
      useFilterStore.getState().setExcludedGenres(['恐怖']);
      useFilterStore.getState().setSelectedRegions(['美国']);
      useFilterStore.getState().setSearchQuery('测试');
      useFilterStore.getState().setSortBy('year');
      useFilterStore.getState().setSortOrder('asc');

      useFilterStore.getState().resetFilters();

      const state = useFilterStore.getState();
      expect(state.type).toBe(defaultFilters.type);
      expect(state.minRating).toBe(defaultFilters.minRating);
      expect(state.maxRating).toBe(defaultFilters.maxRating);
      expect(state.minRatingCount).toBe(defaultFilters.minRatingCount);
      expect(state.minYear).toBe(defaultFilters.minYear);
      expect(state.maxYear).toBe(defaultFilters.maxYear);
      expect(state.selectedGenres).toEqual(defaultFilters.selectedGenres);
      expect(state.excludedGenres).toEqual(defaultFilters.excludedGenres);
      expect(state.selectedRegions).toEqual(defaultFilters.selectedRegions);
      expect(state.searchQuery).toBe(defaultFilters.searchQuery);
      expect(state.sortBy).toBe(defaultFilters.sortBy);
      expect(state.sortOrder).toBe(defaultFilters.sortOrder);
    });

    it('should reset committedFilters immediately without debounce', () => {
      useFilterStore.getState().setType('movie');
      useFilterStore.getState().setMinRating(8);

      useFilterStore.getState().resetFilters();

      const state = useFilterStore.getState();
      expect(state.committedFilters.type).toBe(defaultFilters.type);
      expect(state.committedFilters.minRating).toBe(defaultFilters.minRating);
    });
  });
});
