import React, { useState } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon, FunnelIcon } from '@heroicons/react/24/outline';
import { useFilterStore } from '../store/useFilterStore';

const ALL_GENRES = [
  '剧情', '喜剧', '爱情', '动作', '惊悚', '犯罪', '恐怖', '动画',
  '纪录片', '短片', '悬疑', '冒险', '科幻', '奇幻', '家庭', '音乐',
  '历史', '战争', '歌舞', '传记', '古装', '真人秀', '同性', '运动',
  '西部', '情色', '儿童', '武侠', '脱口秀', '黑色电影', '戏曲', '灾难'
];

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
    selectedGenres,
    sortBy,
    sortOrder,
    setType,
    setMinRating,
    setMaxRating,
    setMinRatingCount,
    toggleGenre,
    clearGenres,
    setSortBy,
    setSortOrder,
    resetFilters,
  } = useFilterStore();

  const FilterContent = () => (
    <div className="space-y-6">
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
            电视剧
          </button>
        </div>
      </div>

      {/* Rating Range */}
      <div>
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">评分范围</h3>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="text-xs text-gray-600 dark:text-gray-400">最低</label>
            <input
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
            <label className="text-xs text-gray-600 dark:text-gray-400">最高</label>
            <input
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

      {/* Rating Count */}
      <div>
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">最低评分人数</h3>
        <input
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
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">排序</h3>
        <div className="flex gap-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="rating">评分</option>
            <option value="rating_count">评分人数</option>
            <option value="year">年份</option>
            <option value="title">标题</option>
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
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">类型筛选 (AND)</h3>
          {selectedGenres.length > 0 && (
            <button
              onClick={clearGenres}
              className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
            >
              清除 ({selectedGenres.length})
            </button>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          {ALL_GENRES.map((genre) => (
            <button
              key={genre}
              onClick={() => toggleGenre(genre)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                selectedGenres.includes(genre)
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {genre}
            </button>
          ))}
        </div>
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
            
            <FilterContent />
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
          
          <FilterContent />
        </div>
      </aside>
    </>
  );
};
