import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render } from '@testing-library/react';
import App from './App';

const useThemeMock = vi.fn();

vi.mock('./components/MovieGrid', () => ({
  MovieGrid: () => <div data-testid="movie-grid" />,
}));

vi.mock('./components/FilterSidebar', () => ({
  FilterSidebar: () => <div data-testid="filter-sidebar" />,
}));

vi.mock('./components/ThemeToggle', () => ({
  ThemeToggle: () => <div data-testid="theme-toggle" />,
}));

vi.mock('./components/NotificationToast', () => ({
  NotificationToast: () => null,
}));

vi.mock('./hooks/useTheme', () => ({
  useTheme: () => useThemeMock(),
}));

vi.mock('./store/useFilterStore', () => ({
  useFilterStore: () => ({ resetFilters: vi.fn() }),
}));

vi.mock('./hooks/useUrlSync', () => ({
  useUrlSync: vi.fn(),
}));

describe('App branding', () => {
  beforeEach(() => {
    useThemeMock.mockReset();
  });

  it('renders logo with webp source and png fallback', () => {
    useThemeMock.mockReturnValue({ theme: 'light', setTheme: vi.fn(), isDark: false });
    const { container } = render(<App />);

    const picture = container.querySelector('picture');
    expect(picture).toBeInTheDocument();

    const source = picture?.querySelector('source');
    expect(source).toHaveAttribute('srcset', '/logo.webp');
    expect(source).toHaveAttribute('type', 'image/webp');

    const img = picture?.querySelector('img');
    expect(img).toHaveAttribute('src', '/logo.png');
  });

  it('uses same logo regardless of theme', () => {
    useThemeMock.mockReturnValue({ theme: 'light', setTheme: vi.fn(), isDark: false });
    const { container, rerender } = render(<App />);

    const imgLight = container.querySelector('picture img');
    expect(imgLight).toHaveAttribute('src', '/logo.png');

    // Switch to dark theme
    useThemeMock.mockReturnValue({ theme: 'dark', setTheme: vi.fn(), isDark: true });
    rerender(<App />);

    const imgDark = container.querySelector('picture img');
    expect(imgDark).toHaveAttribute('src', '/logo.png');
  });
});
