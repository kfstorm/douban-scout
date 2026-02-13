import React, { useEffect } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { MovieCard } from './MovieCard';
import { useInfiniteScroll } from '../hooks/useInfiniteScroll';
import { moviesApi } from '../services/api';
import { useFilterStore } from '../store/useFilterStore';
import type { Movie } from '../types/movie';

export const MovieGrid: React.FC = () => {
  const {
    type,
    minRating,
    maxRating,
    minRatingCount,
    selectedGenres,
    searchQuery,
    sortBy,
    sortOrder,
  } = useFilterStore();

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage, isLoading, error, refetch } =
    useInfiniteQuery({
      queryKey: [
        'movies',
        type,
        minRating,
        maxRating,
        minRatingCount,
        selectedGenres,
        searchQuery,
        sortBy,
        sortOrder,
      ],
      queryFn: ({ pageParam }) =>
        moviesApi.getMovies({
          cursor: pageParam,
          limit: 20,
          type: type || undefined,
          min_rating: minRating > 0 ? minRating : undefined,
          max_rating: maxRating < 10 ? maxRating : undefined,
          min_rating_count: minRatingCount > 0 ? minRatingCount : undefined,
          genres: selectedGenres.length > 0 ? selectedGenres : undefined,
          search: searchQuery || undefined,
          sort_by: sortBy,
          sort_order: sortOrder,
        }),
      initialPageParam: undefined as string | undefined,
      getNextPageParam: (lastPage) => lastPage.next_cursor,
    });

  const { loadMoreRef } = useInfiniteScroll({
    onLoadMore: fetchNextPage,
    hasMore: !!hasNextPage,
    isLoading: isFetchingNextPage,
  });

  // Refetch when filters change
  useEffect(() => {
    refetch();
  }, [
    type,
    minRating,
    maxRating,
    minRatingCount,
    selectedGenres,
    searchQuery,
    sortBy,
    sortOrder,
    refetch,
  ]);

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden animate-pulse"
          >
            <div className="aspect-[2/3] bg-gray-300 dark:bg-gray-700" />
            <div className="p-4 space-y-3">
              <div className="h-4 bg-gray-300 dark:bg-gray-700 rounded w-3/4" />
              <div className="h-3 bg-gray-300 dark:bg-gray-700 rounded w-1/2" />
              <div className="h-3 bg-gray-300 dark:bg-gray-700 rounded w-1/4" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 dark:text-red-400">加载失败，请稍后重试</p>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600"
        >
          重新加载
        </button>
      </div>
    );
  }

  const movies = data?.pages.flatMap((page) => page.items) ?? [];
  const total = data?.pages[0]?.total ?? 0;

  if (movies.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600 dark:text-gray-400 text-lg">没有找到符合条件的作品</p>
        <p className="text-gray-500 dark:text-gray-500 mt-2">请尝试调整筛选条件</p>
      </div>
    );
  }

  return (
    <div>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
        共找到 {total.toLocaleString()} 部作品
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {movies.map((movie: Movie) => (
          <MovieCard key={movie.id} movie={movie} />
        ))}
      </div>

      {/* Load more trigger */}
      <div ref={loadMoreRef} className="h-10 mt-8 flex items-center justify-center">
        {isFetchingNextPage && (
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
        )}
        {!hasNextPage && movies.length > 0 && (
          <p className="text-gray-500 dark:text-gray-400">已加载全部内容</p>
        )}
      </div>
    </div>
  );
};
