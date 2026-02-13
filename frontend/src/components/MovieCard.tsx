import React from 'react';
import { UsersIcon, InformationCircleIcon } from '@heroicons/react/24/outline';
import { getPosterProxyUrl } from '../services/api';
import type { Movie } from '../types/movie';

interface MovieCardProps {
  movie: Movie;
}

export const MovieCard: React.FC<MovieCardProps> = ({ movie }) => {
  const getRatingColor = (rating: number | null) => {
    if (!rating) return 'bg-gray-400';
    if (rating >= 9) return 'bg-green-500';
    if (rating >= 8) return 'bg-blue-500';
    if (rating >= 7) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  const formatCount = (count: number) => {
    if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
    if (count >= 1000) return `${(count / 1000).toFixed(1)}K`;
    return count.toString();
  };

  const timeAgo = (timestamp: number | null) => {
    if (!timestamp) return '未知';
    const now = new Date();
    const date = new Date(timestamp * 1000);
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return '刚刚';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes} 分钟前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} 小时前`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days} 天前`;
    const months = Math.floor(days / 30);
    if (months < 12) return `${months} 个月前`;
    const years = Math.floor(months / 12);
    return `${years} 年前`;
  };

  return (
    <a
      href={movie.douban_url}
      target="_blank"
      rel="noopener noreferrer"
      className="group block bg-white dark:bg-gray-800 rounded-lg shadow-md hover:shadow-xl transition-shadow duration-300 relative"
    >
      <div className="aspect-[2/3] relative overflow-hidden bg-gray-200 dark:bg-gray-700 rounded-t-lg">
        <img
          src={getPosterProxyUrl(movie.douban_id)}
          alt={movie.title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = 'none';
          }}
        />

        {/* Rating badge */}
        {movie.rating && (
          <div
            className={`absolute top-2 right-2 ${getRatingColor(movie.rating)} text-white text-sm font-bold px-2 py-1 rounded`}
          >
            {movie.rating.toFixed(1)}
          </div>
        )}
      </div>

      {/* Info icon with tooltip - Moved outside overflow-hidden container */}
      <div className="absolute top-2 left-2 group/info z-30">
        <InformationCircleIcon className="w-5 h-5 text-white/70 hover:text-white drop-shadow-md transition-colors cursor-help" />
        <div className="absolute left-0 top-6 w-max max-w-[180px] p-2 bg-gray-900/95 text-white text-xs rounded shadow-lg opacity-0 invisible group-hover/info:opacity-100 group-hover/info:visible transition-all pointer-events-none">
          <div className="mb-1 font-semibold border-b border-white/20 pb-1">作品详情</div>
          <div className="text-gray-300 mt-1">数据更新时间: {timeAgo(movie.updated_at)}</div>
          <div className="text-gray-300 mt-1">评分人数: {movie.rating_count.toLocaleString()}</div>
          <div className="text-gray-300 mt-1 leading-relaxed break-words">
            全部类型: {movie.genres.join(', ') || '无'}
          </div>
        </div>
      </div>

      <div className="p-4">
        <h3 className="font-semibold text-gray-900 dark:text-white line-clamp-2 mb-2 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
          {movie.title}
        </h3>

        <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
          <span>{movie.year || 'N/A'}</span>
          <span className="flex items-center gap-1">
            <UsersIcon className="w-4 h-4" />
            {formatCount(movie.rating_count)}
          </span>
        </div>

        {/* Genres */}
        {movie.genres.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {movie.genres.slice(0, 3).map((genre) => (
              <span
                key={genre}
                className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded"
              >
                {genre}
              </span>
            ))}
            {movie.genres.length > 3 && (
              <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                +{movie.genres.length - 3}
              </span>
            )}
          </div>
        )}
      </div>
    </a>
  );
};
