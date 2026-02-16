import { useState } from 'react';
import { FunnelIcon } from '@heroicons/react/24/outline';
import { MovieGrid } from './components/MovieGrid';
import { FilterSidebar } from './components/FilterSidebar';
import { ThemeToggle } from './components/ThemeToggle';
import { NotificationToast } from './components/NotificationToast';
import { useFilterStore } from './store/useFilterStore';
import { useUrlSync } from './hooks/useUrlSync';
import './App.css';

function App() {
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const { resetFilters } = useFilterStore();
  useUrlSync();

  return (
    <div className="min-h-screen bg-ctp-base transition-colors">
      <NotificationToast />
      {/* Header */}
      <header className="sticky top-0 z-40 bg-ctp-surface0 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <img src="/logo.svg" alt="" className="w-8 h-8" />
              <h1 className="text-xl font-bold text-ctp-text">瓣影寻踪</h1>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsFilterOpen(true)}
                className="lg:hidden p-2 text-ctp-subtext0 hover:bg-ctp-surface1 rounded-lg"
                aria-label="打开筛选"
              >
                <FunnelIcon className="w-5 h-5" />
              </button>
              <button
                onClick={resetFilters}
                className="hidden sm:block px-3 py-2 text-sm text-ctp-subtext0 hover:text-ctp-text"
              >
                重置筛选
              </button>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex gap-6">
          {/* Filter Sidebar */}
          <FilterSidebar isOpen={isFilterOpen} onClose={() => setIsFilterOpen(false)} />

          {/* Movie Grid */}
          <div className="flex-1 min-w-0">
            <MovieGrid />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-ctp-surface0 border-t border-ctp-surface1 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-ctp-subtext0">
            瓣影寻踪 - 基于 FastAPI + React 构建
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
