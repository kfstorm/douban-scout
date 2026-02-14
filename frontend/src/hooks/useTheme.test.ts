import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTheme } from './useTheme';

describe('useTheme', () => {
  const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });
    document.documentElement.classList.remove('dark');
  });

  describe('Initial State', () => {
    it('should use dark theme when localStorage has dark', () => {
      localStorageMock.getItem.mockReturnValue('dark');
      const { result } = renderHook(() => useTheme());
      expect(result.current.isDark).toBe(true);
    });

    it('should use light theme when localStorage has light', () => {
      localStorageMock.getItem.mockReturnValue('light');
      const { result } = renderHook(() => useTheme());
      expect(result.current.isDark).toBe(false);
    });

    it('should use system preference when localStorage is empty', () => {
      localStorageMock.getItem.mockReturnValue(null);
      window.matchMedia = vi.fn().mockImplementation((query: string) => ({
        matches: query === '(prefers-color-scheme: dark)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      const { result } = renderHook(() => useTheme());
      expect(result.current.isDark).toBe(true);
    });

    it('should default to light when localStorage is empty and system prefers light', () => {
      localStorageMock.getItem.mockReturnValue(null);
      window.matchMedia = vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      const { result } = renderHook(() => useTheme());
      expect(result.current.isDark).toBe(false);
    });
  });

  describe('toggleTheme', () => {
    it('should toggle from light to dark', () => {
      localStorageMock.getItem.mockReturnValue('light');
      const { result } = renderHook(() => useTheme());

      act(() => {
        result.current.toggleTheme();
      });

      expect(result.current.isDark).toBe(true);
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('should toggle from dark to light', () => {
      localStorageMock.getItem.mockReturnValue('dark');
      const { result } = renderHook(() => useTheme());

      act(() => {
        result.current.toggleTheme();
      });

      expect(result.current.isDark).toBe(false);
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });

    it('should persist dark theme to localStorage', () => {
      localStorageMock.getItem.mockReturnValue('light');
      const { result } = renderHook(() => useTheme());

      act(() => {
        result.current.toggleTheme();
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith('theme', 'dark');
    });

    it('should persist light theme to localStorage', () => {
      localStorageMock.getItem.mockReturnValue('dark');
      const { result } = renderHook(() => useTheme());

      act(() => {
        result.current.toggleTheme();
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith('theme', 'light');
    });
  });

  describe('DOM class manipulation', () => {
    it('should add dark class to document when theme is dark', () => {
      localStorageMock.getItem.mockReturnValue('dark');
      renderHook(() => useTheme());
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('should remove dark class from document when theme is light', () => {
      localStorageMock.getItem.mockReturnValue('light');
      renderHook(() => useTheme());
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });

    it('should toggle dark class when toggling theme', () => {
      localStorageMock.getItem.mockReturnValue('light');
      const { result } = renderHook(() => useTheme());

      expect(document.documentElement.classList.contains('dark')).toBe(false);

      act(() => {
        result.current.toggleTheme();
      });

      expect(document.documentElement.classList.contains('dark')).toBe(true);

      act(() => {
        result.current.toggleTheme();
      });

      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });
  });
});
