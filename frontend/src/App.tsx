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
    <div className="min-h-screen overflow-x-hidden bg-gray-50 dark:bg-gray-900 transition-colors">
      <NotificationToast />
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">瓣影寻踪</h1>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsFilterOpen(true)}
                className="lg:hidden p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                aria-label="打开筛选"
              >
                <FunnelIcon className="w-5 h-5" />
              </button>
              <button
                onClick={resetFilters}
                className="hidden sm:block px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
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
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500 dark:text-gray-400">
            瓣影寻踪 - 基于 FastAPI + React 构建
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
