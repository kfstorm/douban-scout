import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { parseUrlParams } from './urlParams';

describe('parseUrlParams', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    Object.defineProperty(window, 'location', {
      writable: true,
      value: {
        ...originalLocation,
        search: '',
      },
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      writable: true,
      value: originalLocation,
    });
  });

  it('should return empty object when no URL params', () => {
    const result = parseUrlParams();
    expect(result).toEqual({});
  });

  it('should parse type=movie', () => {
    window.location.search = '?type=movie';
    const result = parseUrlParams();
    expect(result.type).toBe('movie');
  });

  it('should parse type=tv', () => {
    window.location.search = '?type=tv';
    const result = parseUrlParams();
    expect(result.type).toBe('tv');
  });

  it('should parse numeric values', () => {
    window.location.search =
      '?minRating=7&maxRating=9&minRatingCount=1000&minYear=2000&maxYear=2020';
    const result = parseUrlParams();
    expect(result.minRating).toBe(7);
    expect(result.maxRating).toBe(9);
    expect(result.minRatingCount).toBe(1000);
    expect(result.minYear).toBe(2000);
    expect(result.maxYear).toBe(2020);
  });

  it('should parse searchQuery', () => {
    window.location.search = '?searchQuery=test%20query';
    const result = parseUrlParams();
    expect(result.searchQuery).toBe('test query');
  });

  it('should parse sortBy and sortOrder', () => {
    window.location.search = '?sortBy=rating&sortOrder=asc';
    const result = parseUrlParams();
    expect(result.sortBy).toBe('rating');
    expect(result.sortOrder).toBe('asc');
  });

  it('should parse array values', () => {
    window.location.search =
      '?selectedGenres=动作,喜剧&excludedGenres=恐怖&selectedRegions=中国,美国';
    const result = parseUrlParams();
    expect(result.selectedGenres).toEqual(['动作', '喜剧']);
    expect(result.excludedGenres).toEqual(['恐怖']);
    expect(result.selectedRegions).toEqual(['中国', '美国']);
  });

  it('should ignore invalid sortBy values', () => {
    window.location.search = '?sortBy=invalid';
    const result = parseUrlParams();
    expect(result.sortBy).toBeUndefined();
  });

  it('should ignore invalid sortOrder values', () => {
    window.location.search = '?sortOrder=invalid';
    const result = parseUrlParams();
    expect(result.sortOrder).toBeUndefined();
  });

  it('should parse multiple params at once', () => {
    window.location.search = '?type=movie&minRating=8&selectedGenres=动作&sortBy=rating';
    const result = parseUrlParams();
    expect(result.type).toBe('movie');
    expect(result.minRating).toBe(8);
    expect(result.selectedGenres).toEqual(['动作']);
    expect(result.sortBy).toBe('rating');
  });
});
