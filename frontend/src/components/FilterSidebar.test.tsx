import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FilterSidebar } from './FilterSidebar';
import { useFilterStore } from '../store/useFilterStore';

vi.mock('../services/api', () => ({
  moviesApi: {
    getGenres: vi.fn().mockResolvedValue([]),
    getRegions: vi.fn().mockResolvedValue([]),
  },
}));

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

const CURRENT_YEAR = new Date().getFullYear();

describe('FilterSidebar - Year Range', () => {
  beforeEach(() => {
    useFilterStore.setState(useFilterStore.getInitialState());
  });

  it('should have year inputs disabled by default', () => {
    renderWithProviders(<FilterSidebar isOpen={true} onClose={vi.fn()} />);

    const minYearInput = document.getElementById('min-year-input') as HTMLInputElement;
    const maxYearInput = document.getElementById('max-year-input') as HTMLInputElement;

    expect(minYearInput.value).toBe('');
    expect(maxYearInput.value).toBe('');
    expect(minYearInput).toBeDisabled();
    expect(maxYearInput).toBeDisabled();
  });

  it('should toggle min year filter state', () => {
    renderWithProviders(<FilterSidebar isOpen={true} onClose={vi.fn()} />);

    const toggle = document.getElementById('min-year-toggle') as HTMLInputElement;
    toggle.click();

    expect(useFilterStore.getState().minYear).toBe(CURRENT_YEAR);

    toggle.click();
    expect(useFilterStore.getState().minYear).toBeNull();
  });

  it('should toggle max year filter state', () => {
    renderWithProviders(<FilterSidebar isOpen={true} onClose={vi.fn()} />);

    const toggle = document.getElementById('max-year-toggle') as HTMLInputElement;
    toggle.click();

    expect(useFilterStore.getState().maxYear).toBe(CURRENT_YEAR);

    toggle.click();
    expect(useFilterStore.getState().maxYear).toBeNull();
  });
});
