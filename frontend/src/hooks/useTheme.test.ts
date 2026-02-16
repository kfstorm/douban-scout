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
  });

  describe('Initial State', () => {
    it('should use dark theme when localStorage has dark', () => {
      localStorageMock.getItem.mockReturnValue('dark');
      const { result } = renderHook(() => useTheme());
      expect(result.current.theme).toBe('dark');
      expect(result.current.isDark).toBe(true);
    });

    it('should use light theme when localStorage has light', () => {
      localStorageMock.getItem.mockReturnValue('light');
      const { result } = renderHook(() => useTheme());
      expect(result.current.theme).toBe('light');
      expect(result.current.isDark).toBe(false);
    });

    it('should default to system when localStorage is empty', () => {
      localStorageMock.getItem.mockReturnValue(null);
      const { result } = renderHook(() => useTheme());
      expect(result.current.theme).toBe('system');
    });

    it('should use system dark preference when theme is system', () => {
      localStorageMock.getItem.mockReturnValue('system');
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
  });

  describe('toggleTheme', () => {
    it('should cycle through system -> light -> dark', () => {
      localStorageMock.getItem.mockReturnValue('system');
      const { result } = renderHook(() => useTheme());
      expect(result.current.theme).toBe('system');

      act(() => {
        result.current.toggleTheme();
      });
      expect(result.current.theme).toBe('light');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('theme', 'light');

      act(() => {
        result.current.toggleTheme();
      });
      expect(result.current.theme).toBe('dark');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('theme', 'dark');

      act(() => {
        result.current.toggleTheme();
      });
      expect(result.current.theme).toBe('system');
      expect(localStorageMock.setItem).toHaveBeenCalledWith('theme', 'system');
    });
  });

  describe('DOM class manipulation', () => {
    it('should add dark and mocha classes to document when theme is dark', () => {
      localStorageMock.getItem.mockReturnValue('dark');
      renderHook(() => useTheme());
      expect(document.documentElement.classList.contains('dark')).toBe(true);
      expect(document.documentElement.classList.contains('mocha')).toBe(true);
      expect(document.documentElement.classList.contains('latte')).toBe(false);
    });

    it('should remove dark and mocha classes and add latte from document when theme is light', () => {
      localStorageMock.getItem.mockReturnValue('light');
      renderHook(() => useTheme());
      expect(document.documentElement.classList.contains('dark')).toBe(false);
      expect(document.documentElement.classList.contains('mocha')).toBe(false);
      expect(document.documentElement.classList.contains('latte')).toBe(true);
    });

    it('should handle system theme changes', () => {
      let changeHandler: (() => void) | undefined;
      const mediaQueryMock = {
        matches: false,
        media: '(prefers-color-scheme: dark)',
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn((event, handler) => {
          if (event === 'change') changeHandler = handler;
        }),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      } as unknown as MediaQueryList;
      window.matchMedia = vi.fn().mockReturnValue(mediaQueryMock);

      localStorageMock.getItem.mockReturnValue('system');
      renderHook(() => useTheme());

      expect(document.documentElement.classList.contains('dark')).toBe(false);
      expect(document.documentElement.classList.contains('mocha')).toBe(false);
      expect(document.documentElement.classList.contains('latte')).toBe(true);

      // Simulate system change to dark
      act(() => {
        Object.defineProperty(mediaQueryMock, 'matches', { value: true });
        if (changeHandler) changeHandler();
      });

      expect(document.documentElement.classList.contains('dark')).toBe(true);
      expect(document.documentElement.classList.contains('mocha')).toBe(true);
      expect(document.documentElement.classList.contains('latte')).toBe(false);
    });
  });
});
