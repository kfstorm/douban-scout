import { useState, useEffect } from 'react';
import { FunnelIcon } from '@heroicons/react/24/outline';
import { MovieGrid } from './components/MovieGrid';
import { FilterSidebar } from './components/FilterSidebar';
import { SearchBar } from './components/SearchBar';
import { ThemeToggle } from './components/ThemeToggle';
import { ImportStatusBanner } from './components/ImportStatus';
import { useFilterStore } from './store/useFilterStore';
import { importApi } from './services/api';
import type { ImportStatus } from './types/movie';
import './App.css';

function App() {
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [importStatus, setImportStatus] = useState<ImportStatus>({
    status: 'idle',
    processed: 0,
    total: 0,
    percentage: 0,
    message: null,
    started_at: null,
    completed_at: null,
  });
  const { resetFilters } = useFilterStore();

  // Poll import status
  useEffect(() => {
    const pollStatus = async () => {
      try {
        const status = await importApi.getStatus();
        setImportStatus(status);
      } catch (error) {
        console.error('Failed to fetch import status:', error);
      }
    };

    // Initial check
    pollStatus();

    // Poll every 2 seconds if import is running
    const interval = setInterval(() => {
      if (importStatus.status === 'running') {
        pollStatus();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [importStatus.status]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">豆瓣影视探索</h1>
            </div>

            {/* Search - Desktop */}
            <div className="hidden md:flex flex-1 max-w-md mx-8">
              <SearchBar />
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsFilterOpen(true)}
                className="lg:hidden p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
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

          {/* Search - Mobile */}
          <div className="md:hidden pb-4">
            <SearchBar />
          </div>
        </div>
      </header>

      {/* Import Status Banner */}
      {importStatus.status !== 'idle' && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <ImportStatusBanner status={importStatus} />
        </div>
      )}

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
            豆瓣影视探索 - 基于 FastAPI + React 构建
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
