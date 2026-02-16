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

describe('App branding by theme', () => {
  beforeEach(() => {
    useThemeMock.mockReset();
    document.querySelectorAll("link[rel='icon']").forEach((link) => link.remove());
  });

  it('uses light logo and favicon in light mode', () => {
    useThemeMock.mockReturnValue({ theme: 'light', setTheme: vi.fn(), isDark: false });
    const { container } = render(<App />);

    const logo = container.querySelector('img');
    expect(logo).toHaveAttribute('src', '/logo-light.svg');

    const favicon = document.querySelector("link[rel='icon']");
    expect(favicon).toBeInTheDocument();
    expect(favicon).toHaveAttribute('href', '/logo-light.svg');
  });

  it('uses dark logo and favicon in dark mode', () => {
    useThemeMock.mockReturnValue({ theme: 'dark', setTheme: vi.fn(), isDark: true });
    const { container } = render(<App />);

    const logo = container.querySelector('img');
    expect(logo).toHaveAttribute('src', '/logo-dark.svg');

    const favicon = document.querySelector("link[rel='icon']");
    expect(favicon).toBeInTheDocument();
    expect(favicon).toHaveAttribute('href', '/logo-dark.svg');
  });

  it('updates logo and favicon when theme changes', () => {
    const themeState = { theme: 'light', setTheme: vi.fn(), isDark: false };
    useThemeMock.mockImplementation(() => themeState);

    const { container, rerender } = render(<App />);

    expect(container.querySelector('img')).toHaveAttribute('src', '/logo-light.svg');
    expect(document.querySelector("link[rel='icon']")).toHaveAttribute('href', '/logo-light.svg');

    themeState.theme = 'dark';
    themeState.isDark = true;
    rerender(<App />);

    expect(container.querySelector('img')).toHaveAttribute('src', '/logo-dark.svg');
    expect(document.querySelector("link[rel='icon']")).toHaveAttribute('href', '/logo-dark.svg');
  });
});
