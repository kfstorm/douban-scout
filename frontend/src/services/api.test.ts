import { describe, it, expect } from 'vitest';

describe('getPosterProxyUrl', () => {
  it('should return correct poster URL', async () => {
    // Import dynamically to avoid module initialization issues
    const { getPosterProxyUrl } = await import('./api');
    const url = getPosterProxyUrl(1291543);
    expect(url).toContain('/movies/1291543/poster');
  });

  it('should handle different movie IDs', async () => {
    const { getPosterProxyUrl } = await import('./api');
    expect(getPosterProxyUrl(1)).toContain('/movies/1/poster');
    expect(getPosterProxyUrl(999999)).toContain('/movies/999999/poster');
  });
});

// Note: Testing the axios-based methods (moviesApi.*) requires more complex mocking
// of the axios module. These tests verify that the API module can be imported
// and basic utilities work. Full API integration tests should be done in e2e tests.
