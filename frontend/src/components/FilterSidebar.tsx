import React, { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import {
  XMarkIcon,
  FunnelIcon,
  InformationCircleIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import { useFilterStore } from '../store/useFilterStore';
import { moviesApi } from '../services/api';
import { SearchBar } from './SearchBar';

const MAX_REGION_DISPLAY_ITEMS = 20;

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
    selectedRegions,
    sortBy,
    sortOrder,
    committedFilters,
    setType,
    setMinRating,
    setMaxRating,
    setMinRatingCount,
    setMinYear,
    setMaxYear,
    toggleRegion,
    clearRegions,
    clearGenres,
    cycleGenre,
    clearExcludedGenres,
    setSortBy,
    setSortOrder,
    resetFilters,
  } = useFilterStore();

  const [regionSearch, setRegionSearch] = useState('');
  const [genreSearch, setGenreSearch] = useState('');
  const [effectiveRegionSearch, setEffectiveRegionSearch] = useState('');
  const [effectiveGenreSearch, setEffectiveGenreSearch] = useState('');
  const [isRegionComposing, setIsRegionComposing] = useState(false);
  const [isGenreComposing, setIsGenreComposing] = useState(false);

  // Sync effective search with local search when not composing
  useEffect(() => {
    if (isRegionComposing) return;

    const timer = setTimeout(() => {
      setEffectiveRegionSearch(regionSearch);
    }, 150);

    return () => clearTimeout(timer);
  }, [regionSearch, isRegionComposing]);

  useEffect(() => {
    if (isGenreComposing) return;

    const timer = setTimeout(() => {
      setEffectiveGenreSearch(genreSearch);
    }, 150);

    return () => clearTimeout(timer);
  }, [genreSearch, isGenreComposing]);

  // Fetch genres from backend (use committedFilters to avoid initial empty requests)
  const { data: genresData, isLoading: isLoadingGenres } = useQuery({
    queryKey: ['genres', committedFilters.type],
    queryFn: () => moviesApi.getGenres(committedFilters.type || undefined),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Fetch regions from backend (use committedFilters to avoid initial empty requests)
  const { data: regionsData, isLoading: isLoadingRegions } = useQuery({
    queryKey: ['regions', committedFilters.type],
    queryFn: () => moviesApi.getRegions(committedFilters.type || undefined),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const content = (
    <div className="space-y-6">
      {/* Title Search */}
      <div>
        <h3 className="text-sm font-medium text-ctp-text mb-3">标题搜索</h3>
        <SearchBar />
      </div>

      {/* Type Filter */}
      <div>
        <h3 className="text-sm font-medium text-ctp-text mb-3">类型</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setType(null)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              type === null
                ? 'bg-ctp-mauve text-ctp-base'
                : 'bg-ctp-surface1 text-ctp-subtext1 hover:bg-ctp-surface2'
            }`}
          >
            全部
          </button>
          <button
            onClick={() => setType('movie')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              type === 'movie'
                ? 'bg-ctp-mauve text-ctp-base'
                : 'bg-ctp-surface1 text-ctp-subtext1 hover:bg-ctp-surface2'
            }`}
          >
            电影
          </button>
          <button
            onClick={() => setType('tv')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              type === 'tv'
                ? 'bg-ctp-mauve text-ctp-base'
                : 'bg-ctp-surface1 text-ctp-subtext1 hover:bg-ctp-surface2'
            }`}
          >
            电视节目
          </button>
        </div>
      </div>

      {/* Rating Range */}
      <div>
        <div className="flex items-center gap-1 mb-3 group relative">
          <h3 className="text-sm font-medium text-ctp-text">评分范围</h3>
          <InformationCircleIcon className="w-4 h-4 text-ctp-overlay0 cursor-help" />
          <div className="absolute left-0 top-6 w-64 max-w-[calc(100vw-4rem)] px-3 py-2 bg-ctp-crust text-ctp-text text-xs rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-opacity z-10">
            最低评分设为 0 时将包含未评分的作品
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label htmlFor="min-rating" className="text-xs text-ctp-subtext0">
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
              className="w-full mt-1 px-3 py-2 border border-ctp-surface1 rounded-lg bg-ctp-surface0 text-ctp-text"
            />
          </div>
          <span className="text-ctp-overlay0">-</span>
          <div className="flex-1">
            <label htmlFor="max-rating" className="text-xs text-ctp-subtext0">
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
              className="w-full mt-1 px-3 py-2 border border-ctp-surface1 rounded-lg bg-ctp-surface0 text-ctp-text"
            />
          </div>
        </div>
      </div>

      {/* Year Range */}
      <div>
        <h3 className="text-sm font-medium text-ctp-text mb-3">年份范围</h3>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label htmlFor="min-year" className="text-xs text-ctp-subtext0">
              起始
            </label>
            <input
              id="min-year"
              type="number"
              value={minYear || ''}
              onChange={(e) => setMinYear(parseInt(e.target.value) || null)}
              className="w-full mt-1 px-3 py-2 border border-ctp-surface1 rounded-lg bg-ctp-surface0 text-ctp-text"
            />
          </div>
          <span className="text-ctp-overlay0">-</span>
          <div className="flex-1">
            <label htmlFor="max-year" className="text-xs text-ctp-subtext0">
              结束
            </label>
            <input
              id="max-year"
              type="number"
              value={maxYear || ''}
              onChange={(e) => setMaxYear(parseInt(e.target.value) || null)}
              className="w-full mt-1 px-3 py-2 border border-ctp-surface1 rounded-lg bg-ctp-surface0 text-ctp-text"
            />
          </div>
        </div>
      </div>

      {/* Rating Count */}
      <div>
        <label htmlFor="min-rating-count" className="block text-sm font-medium text-ctp-text mb-3">
          最低评分人数
        </label>
        <input
          id="min-rating-count"
          type="number"
          min="0"
          step="1000"
          value={minRatingCount}
          onChange={(e) => setMinRatingCount(parseInt(e.target.value) || 0)}
          className="w-full px-3 py-2 border border-ctp-surface1 rounded-lg bg-ctp-surface0 text-ctp-text"
        />
      </div>

      {/* Sort */}
      <div>
        <label htmlFor="sort-by" className="block text-sm font-medium text-ctp-text mb-3">
          排序
        </label>
        <div className="flex gap-2">
          <select
            id="sort-by"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'rating' | 'rating_count' | 'year')}
            className="flex-1 px-3 py-2 border border-ctp-surface1 rounded-lg bg-ctp-surface0 text-ctp-text"
          >
            <option value="rating_count">评分人数</option>
            <option value="rating">评分</option>
            <option value="year">年份</option>
          </select>
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="px-3 py-2 border border-ctp-surface1 rounded-lg bg-ctp-surface0 text-ctp-text"
          >
            {sortOrder === 'asc' ? '↑' : '↓'}
          </button>
        </div>
      </div>

      {/* Regions */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-ctp-text">地区筛选</h3>
          {selectedRegions.length > 0 && (
            <button onClick={clearRegions} className="text-xs text-ctp-mauve hover:underline">
              清除 ({selectedRegions.length})
            </button>
          )}
        </div>

        {/* Region Search */}
        <div className="relative mb-3">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ctp-overlay0" />
          <input
            type="text"
            placeholder="搜索地区..."
            value={regionSearch}
            onChange={(e) => setRegionSearch(e.target.value)}
            onCompositionStart={() => setIsRegionComposing(true)}
            onCompositionEnd={() => setIsRegionComposing(false)}
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-ctp-surface1 rounded-lg bg-ctp-base text-ctp-text placeholder-ctp-overlay0 focus:outline-hidden focus:ring-1 focus:ring-ctp-mauve"
          />
        </div>

        <div className="max-h-48 overflow-y-auto pr-2 -mr-2">
          {isLoadingRegions ? (
            <div className="flex flex-wrap gap-2">
              {Array.from({ length: 10 }).map((_, i) => (
                <div
                  key={i}
                  className="px-3 py-1 rounded-full text-xs bg-ctp-surface1 animate-pulse w-12 h-6"
                />
              ))}
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {regionsData
                ?.filter((r) =>
                  r.region.toLowerCase().includes(effectiveRegionSearch.toLowerCase()),
                )
                .slice(0, MAX_REGION_DISPLAY_ITEMS)
                .map((regionItem) => {
                  const isSelected = selectedRegions.includes(regionItem.region);

                  return (
                    <button
                      key={regionItem.region}
                      onClick={() => toggleRegion(regionItem.region)}
                      className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                        isSelected
                          ? 'bg-ctp-mauve text-ctp-base'
                          : 'bg-ctp-surface1 text-ctp-subtext1 hover:bg-ctp-surface2'
                      }`}
                      title={`${regionItem.region}: ${regionItem.count} 部作品`}
                    >
                      {regionItem.region}
                    </button>
                  );
                })}
            </div>
          )}
        </div>
      </div>

      {/* Genres */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex flex-col gap-1">
            <h3 className="text-sm font-medium text-ctp-text">类型筛选</h3>
            <p className="text-[10px] text-ctp-overlay0">点击切换：未选中 → 包含 → 排除</p>
          </div>
          {(selectedGenres.length > 0 || excludedGenres.length > 0) && (
            <button
              onClick={() => {
                clearGenres();
                clearExcludedGenres();
              }}
              className="text-xs text-ctp-mauve hover:underline"
            >
              清除 ({selectedGenres.length + excludedGenres.length})
            </button>
          )}
        </div>

        {/* Genre Search */}
        <div className="relative mb-3">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ctp-overlay0" />
          <input
            type="text"
            placeholder="搜索类型..."
            value={genreSearch}
            onChange={(e) => setGenreSearch(e.target.value)}
            onCompositionStart={() => setIsGenreComposing(true)}
            onCompositionEnd={() => setIsGenreComposing(false)}
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-ctp-surface1 rounded-lg bg-ctp-base text-ctp-text placeholder-ctp-overlay0 focus:outline-hidden focus:ring-1 focus:ring-ctp-mauve"
          />
        </div>

        <div className="max-h-48 overflow-y-auto pr-2 -mr-2">
          {isLoadingGenres ? (
            <div className="flex flex-wrap gap-2">
              {Array.from({ length: 10 }).map((_, i) => (
                <div
                  key={i}
                  className="px-3 py-1 rounded-full text-xs bg-ctp-surface1 animate-pulse w-12 h-6"
                />
              ))}
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {genresData
                ?.filter((g) => g.genre.toLowerCase().includes(effectiveGenreSearch.toLowerCase()))
                .map((genreItem) => {
                  const isSelected = selectedGenres.includes(genreItem.genre);
                  const isExcluded = excludedGenres.includes(genreItem.genre);

                  return (
                    <button
                      key={genreItem.genre}
                      onClick={() => cycleGenre(genreItem.genre)}
                      className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                        isSelected
                          ? 'bg-ctp-mauve text-ctp-base'
                          : isExcluded
                            ? 'bg-ctp-red text-ctp-base'
                            : 'bg-ctp-surface1 text-ctp-subtext1 hover:bg-ctp-surface2'
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
      </div>

      {/* Reset */}
      <button
        onClick={resetFilters}
        className="w-full px-4 py-2 bg-ctp-surface1 text-ctp-subtext1 rounded-lg hover:bg-ctp-surface2 transition-colors"
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
          <Dialog.Panel className="w-full max-w-sm bg-ctp-base h-full p-6 overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <Dialog.Title className="text-lg font-semibold text-ctp-text flex items-center gap-2">
                <FunnelIcon className="w-5 h-5" />
                筛选
              </Dialog.Title>
              <button
                onClick={onClose}
                className="p-2 text-ctp-overlay0 hover:text-ctp-subtext0"
                aria-label="关闭筛选"
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
        <div className="sticky top-22 bg-ctp-surface0 rounded-lg shadow-md p-6 max-h-[calc(100vh-7rem)] overflow-y-auto">
          <h2 className="text-lg font-semibold text-ctp-text mb-6 flex items-center gap-2">
            <FunnelIcon className="w-5 h-5" />
            筛选
          </h2>

          {content}
        </div>
      </aside>
    </>
  );
};
