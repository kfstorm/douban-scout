# AGENTS.md - Frontend

> For project overview and high-level information, see [../AGENTS.md](../AGENTS.md)

This document provides guidelines for AI agents working on the **frontend** codebase (React + TypeScript).

## Tech Stack

- **Framework**: React 18
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **State Management**: TanStack Query (server) + Zustand (client)
- **Build Tool**: Vite
- **Package Manager**: npm

## Build Commands

```bash
# Navigate to frontend directory (all commands assume you're in frontend/)
cd frontend

# Install dependencies
npm install

# Run development server (port 3000, proxies /api to backend:8000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Code Style Guidelines

### Imports

- Use absolute imports for internal modules
- Separate imports by type: React → external libraries → internal components/hooks

```typescript
import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

import { MovieGrid } from './components/MovieGrid';
import { FilterSidebar } from './components/FilterSidebar';
import { useFilterStore } from './store/useFilterStore';
import { moviesApi, type MoviesParams } from './services/api';
```

### TypeScript Configuration

- `strict: true` enabled in `tsconfig.json`
- Enable: `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`
- Use `.tsx` for React components, `.ts` for utilities

### Component Patterns

- Functional components with hooks
- Type props with TypeScript interfaces
- Use TanStack Query for server state
- Use Zustand for client state (filters, theme)

```typescript
interface MovieCardProps {
  movie: Movie;
  onClick?: (movie: Movie) => void;
}

export function MovieCard({ movie, onClick }: MovieCardProps) {
  return (
    <div className="movie-card" onClick={() => onClick?.(movie)}>
      <img src={movie.poster_url} alt={movie.title} />
    </div>
  );
}
```

### Naming Conventions

- Components: `PascalCase` (e.g., `MovieGrid`, `FilterSidebar`)
- Files: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Hooks: `camelCase` starting with `use` (e.g., `useDebounce`)
- State stores: `useStoreName` (e.g., `useFilterStore`)

### Tailwind CSS

- Use utility classes for styling
- Support dark mode with `dark:` prefix
- Responsive design with `sm:`, `md:`, `lg:` prefixes

```tsx
<div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
  <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg">
    Click me
  </button>
</div>
```

## Testing

- No test framework configured yet
- If adding tests, use Vitest or Jest with React Testing Library

## Type Checking

```bash
# Type check (runs as part of build)
npm run build

# No ESLint configured yet
```

## File Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── MovieGrid.tsx
│   │   ├── FilterSidebar.tsx
│   │   ├── SearchBar.tsx
│   │   └── ...
│   ├── hooks/               # Custom hooks
│   ├── services/            # API services
│   │   └── api.ts
│   ├── store/              # Zustand stores
│   │   └── useFilterStore.ts
│   ├── types/              # TypeScript types
│   │   └── movie.ts
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

## UX Wording Guidelines

- **No English text**: All user-facing text must be in Chinese
- **Use inclusive terms**: The app covers both movies and TV shows
  - Use "作品" or "影视" instead of "电影" 
  - Use "电视节目" instead of "电视剧"
- Examples:
  - ✓ 搜索作品标题... / 共找到 100 部作品
  - ✗ 搜索电影标题... / 共找到 100 部电影
  - ✓ 类型: 全部 / 影视 / 电视节目
  - ✗ 类型: 全部 / 电影 / 电视剧

## Key Patterns

### State Management

- **Zustand**: For filter state (persisted to localStorage)
- **TanStack Query**: For API data (caching, refetching)
- **Dark mode**: Toggle with system preference detection

### API Integration

- Base API URL: `/api` (proxied to backend:8000 in dev)
- Use TanStack Query for all API calls
- Handle loading and error states consistently
