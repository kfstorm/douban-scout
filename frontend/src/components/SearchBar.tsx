import React, { useState, useEffect } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { useFilterStore } from '../store/useFilterStore';

export const SearchBar: React.FC = () => {
  const { searchQuery, setSearchQuery } = useFilterStore();
  const [localQuery, setLocalQuery] = useState(searchQuery);
  const [isComposing, setIsComposing] = useState(false);

  // Sync local query with store query (e.g. on initial load from URL)
  useEffect(() => {
    setLocalQuery(searchQuery);
  }, [searchQuery]);

  useEffect(() => {
    if (isComposing) return;

    // Avoid triggering if localQuery is already in sync with store
    if (localQuery === searchQuery) return;

    const timer = setTimeout(() => {
      setSearchQuery(localQuery);
    }, 300);

    return () => clearTimeout(timer);
  }, [localQuery, isComposing, setSearchQuery, searchQuery]);

  return (
    <div className="relative">
      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <MagnifyingGlassIcon className="h-5 w-5 text-ctp-overlay0" />
      </div>
      <input
        type="text"
        value={localQuery}
        onChange={(e) => setLocalQuery(e.target.value)}
        onCompositionStart={() => setIsComposing(true)}
        onCompositionEnd={() => setIsComposing(false)}
        placeholder="搜索作品标题..."
        className="block w-full pl-10 pr-3 py-2 border border-ctp-surface1 rounded-lg leading-5 bg-ctp-surface0 text-ctp-text placeholder-ctp-overlay0 focus:outline-hidden focus:ring-2 focus:ring-ctp-mauve focus:border-ctp-mauve transition-colors"
      />
    </div>
  );
};
