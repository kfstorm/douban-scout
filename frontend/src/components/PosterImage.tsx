import React, { useState } from 'react';
import { PhotoIcon } from '@heroicons/react/24/outline';
import { getPosterProxyUrl } from '../services/api';

interface PosterImageProps {
  id: number;
  title: string;
  className?: string;
}

export const PosterImage: React.FC<PosterImageProps> = ({ id, title, className = '' }) => {
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  if (error) {
    return (
      <div
        className={`flex flex-col items-center justify-center bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 ${className}`}
      >
        <PhotoIcon className="w-12 h-12 mb-2" />
        <span className="text-xs px-2 text-center">暂无海报</span>
      </div>
    );
  }

  return (
    <div className={`relative overflow-hidden bg-gray-200 dark:bg-gray-700 ${className}`}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}
      <img
        src={getPosterProxyUrl(id)}
        alt={title}
        className={`w-full h-full object-cover transition-opacity duration-300 ${loading ? 'opacity-0' : 'opacity-100'}`}
        onLoad={() => setLoading(false)}
        onError={() => {
          setLoading(false);
          setError(true);
        }}
      />
    </div>
  );
};
