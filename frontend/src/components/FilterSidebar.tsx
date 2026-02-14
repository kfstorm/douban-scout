import React from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon, FunnelIcon, InformationCircleIcon } from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import { useFilterStore } from '../store/useFilterStore';
import { moviesApi } from '../services/api';
import { SearchBar } from './SearchBar';

interface FilterSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const FilterSidebar: React.FC<FilterSidebarProps> = ({ isOpen, onClose }) => {
  const {
    type,
    minRating,
    maxRating,
    minRatingCount,
    minYear,
    maxYear,
    selectedGenres,
    excludedGenres,
    sortBy,
    sortOrder,
    setType,
    setMinRating,
    setMaxRating,
    setMinRatingCount,
    setMinYear,
    setMaxYear,
    clearGenres,
    cycleGenre,
    clearExcludedGenres,
    setSortBy,
    setSortOrder,
    resetFilters,
  } = useFilterStore();

  // Fetch genres from backend
  const { data: genresData, isLoading: isLoadingGenres } = useQuery({
    queryKey: ['genres', type],
    queryFn: () => moviesApi.getGenres(type || undefined),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const content = (
    <div className="space-y-6">
      {/* Title Search */}
      <div>
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">标题搜索</h3>
        <SearchBar />
      </div>

      {/* Type Filter */}
      <div>
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">类型</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setType(null)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              type === null
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            全部
          </button>
          <button
            onClick={() => setType('movie')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              type === 'movie'
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            电影
          </button>
          <button
            onClick={() => setType('tv')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              type === 'tv'
                ? 'bg-primary-500 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            电视节目
          </button>
        </div>
      </div>

      {/* Rating Range */}
      <div>
        <div className="flex items-center gap-1 mb-3 group relative">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">评分范围</h3>
          <InformationCircleIcon className="w-4 h-4 text-gray-400 cursor-help" />
          <div className="absolute left-0 top-6 w-64 px-3 py-2 bg-gray-800 text-white text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity z-10">
            最低评分设为 0 时将包含未评分的作品
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label htmlFor="min-rating" className="text-xs text-gray-600 dark:text-gray-400">
              最低
            </label>
            <input
              id="min-rating"
              type="number"
              min="0"
              max="10"
              step="0.1"
              value={minRating}
              onChange={(e) => setMinRating(parseFloat(e.target.value) || 0)}
              className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          <span className="text-gray-400">-</span>
          <div className="flex-1">
            <label htmlFor="max-rating" className="text-xs text-gray-600 dark:text-gray-400">
              最高
            </label>
            <input
              id="max-rating"
              type="number"
              min="0"
              max="10"
              step="0.1"
              value={maxRating}
              onChange={(e) => setMaxRating(parseFloat(e.target.value) || 10)}
              className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Year Range */}
      <div>
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">年份范围</h3>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label htmlFor="min-year" className="text-xs text-gray-600 dark:text-gray-400">
              起始
            </label>
            <input
              id="min-year"
              type="number"
              value={minYear || ''}
              onChange={(e) => setMinYear(parseInt(e.target.value) || null)}
              className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
          <span className="text-gray-400">-</span>
          <div className="flex-1">
            <label htmlFor="max-year" className="text-xs text-gray-600 dark:text-gray-400">
              结束
            </label>
            <input
              id="max-year"
              type="number"
              value={maxYear || ''}
              onChange={(e) => setMaxYear(parseInt(e.target.value) || null)}
              className="w-full mt-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>
        </div>
      </div>

      {/* Rating Count */}
      <div>
        <label
          htmlFor="min-rating-count"
          className="block text-sm font-medium text-gray-900 dark:text-white mb-3"
        >
          最低评分人数
        </label>
        <input
          id="min-rating-count"
          type="number"
          min="0"
          step="1000"
          value={minRatingCount}
          onChange={(e) => setMinRatingCount(parseInt(e.target.value) || 0)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        />
      </div>

      {/* Sort */}
      <div>
        <label
          htmlFor="sort-by"
          className="block text-sm font-medium text-gray-900 dark:text-white mb-3"
        >
          排序
        </label>
        <div className="flex gap-2">
          <select
            id="sort-by"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'rating' | 'rating_count' | 'year')}
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="rating">评分</option>
            <option value="rating_count">评分人数</option>
            <option value="year">年份</option>
          </select>
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            {sortOrder === 'asc' ? '↑' : '↓'}
          </button>
        </div>
      </div>

      {/* Genres */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex flex-col gap-1">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white">类型筛选</h3>
            <p className="text-[10px] text-gray-500 dark:text-gray-400">
              点击切换：未选中 → 包含 → 排除
            </p>
          </div>
          {(selectedGenres.length > 0 || excludedGenres.length > 0) && (
            <button
              onClick={() => {
                clearGenres();
                clearExcludedGenres();
              }}
              className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
            >
              清除 ({selectedGenres.length + excludedGenres.length})
            </button>
          )}
        </div>
        {isLoadingGenres ? (
          <div className="flex flex-wrap gap-2">
            {Array.from({ length: 10 }).map((_, i) => (
              <div
                key={i}
                className="px-3 py-1 rounded-full text-xs bg-gray-200 dark:bg-gray-700 animate-pulse w-12 h-6"
              />
            ))}
          </div>
        ) : (
          <div className="flex flex-wrap gap-2">
            {genresData?.map((genreItem) => {
              const isSelected = selectedGenres.includes(genreItem.genre);
              const isExcluded = excludedGenres.includes(genreItem.genre);

              return (
                <button
                  key={genreItem.genre}
                  onClick={() => cycleGenre(genreItem.genre)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    isSelected
                      ? 'bg-primary-500 text-white'
                      : isExcluded
                        ? 'bg-red-500 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                  title={`${genreItem.genre}: ${genreItem.count} 部作品${
                    isSelected ? ' (包含)' : isExcluded ? ' (排除)' : ''
                  }`}
                >
                  {isExcluded && <span className="mr-1">✕</span>}
                  {genreItem.genre}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Reset */}
      <button
        onClick={resetFilters}
        className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
      >
        重置所有筛选
      </button>
    </div>
  );

  return (
    <>
      {/* Mobile Drawer */}
      <Dialog open={isOpen} onClose={onClose} className="lg:hidden relative z-50">
        <div className="fixed inset-0 bg-black/30" aria-hidden="true" />

        <div className="fixed inset-0 flex justify-end">
          <Dialog.Panel className="w-full max-w-sm bg-white dark:bg-gray-900 h-full p-6 overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <Dialog.Title className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <FunnelIcon className="w-5 h-5" />
                筛选
              </Dialog.Title>
              <button
                onClick={onClose}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            {content}
          </Dialog.Panel>
        </div>
      </Dialog>

      {/* Desktop Sidebar */}
      <aside className="hidden lg:block w-72 shrink-0">
        <div className="sticky top-4 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
            <FunnelIcon className="w-5 h-5" />
            筛选
          </h2>

          {content}
        </div>
      </aside>
    </>
  );
};
