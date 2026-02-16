import { useEffect, useState } from 'react';

export type Theme = 'light' | 'dark' | 'system';

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'system';
    const saved = localStorage.getItem('theme') as Theme | null;
    return saved || 'system';
  });

  const [isDark, setIsDark] = useState(() => {
    if (typeof window === 'undefined') return false;
    if (theme === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return theme === 'dark';
  });

  useEffect(() => {
    const root = window.document.documentElement;
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const applyTheme = () => {
      const effectiveTheme = theme === 'system' ? (mediaQuery.matches ? 'dark' : 'light') : theme;
      const isDarkNow = effectiveTheme === 'dark';

      root.classList.toggle('dark', isDarkNow);
      root.classList.toggle('mocha', isDarkNow);
      root.classList.toggle('latte', !isDarkNow);

      setIsDark(isDarkNow);
      localStorage.setItem('theme', theme);
    };

    applyTheme();

    if (theme === 'system') {
      mediaQuery.addEventListener('change', applyTheme);
      return () => mediaQuery.removeEventListener('change', applyTheme);
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => {
      if (prev === 'system') return 'light';
      if (prev === 'light') return 'dark';
      return 'system';
    });
  };

  return { theme, setTheme, isDark, toggleTheme };
}
