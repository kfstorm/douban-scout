import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MovieCard } from './MovieCard';
import type { Movie } from '../types/movie';

vi.mock('./PosterImage', () => ({
  PosterImage: () => <div data-testid="poster-image">poster</div>,
}));

describe('MovieCard', () => {
  const mockMovie: Movie = {
    id: 1291543,
    title: '测试作品',
    year: 2020,
    rating: 8.5,
    rating_count: 150000,
    type: 'movie',
    genres: ['动作', '科幻', '冒险'],
    updated_at: Date.now() / 1000,
  };

  it('should render movie title', () => {
    render(<MovieCard movie={mockMovie} />);
    // Title appears in both main card (heading) and tooltip
    const titles = screen.getAllByText('测试作品');
    expect(titles.length).toBeGreaterThanOrEqual(1);
    // Check that at least one is a heading
    const headingTitle = titles.find((el) => el.tagName === 'H3');
    expect(headingTitle).toBeInTheDocument();
  });

  it('should render year', () => {
    render(<MovieCard movie={mockMovie} />);
    expect(screen.getByText('2020')).toBeInTheDocument();
  });

  it('should render unknown year when year is null', () => {
    const movieWithoutYear = { ...mockMovie, year: null };
    render(<MovieCard movie={movieWithoutYear} />);
    expect(screen.getByText('未知年份')).toBeInTheDocument();
  });

  it('should render rating', () => {
    render(<MovieCard movie={mockMovie} />);
    expect(screen.getByText('8.5')).toBeInTheDocument();
  });

  it('should render 无 when rating is null', () => {
    const movieWithoutRating = { ...mockMovie, rating: null };
    render(<MovieCard movie={movieWithoutRating} />);
    expect(screen.getByText('无')).toBeInTheDocument();
  });

  it('should render rating count formatted', () => {
    render(<MovieCard movie={mockMovie} />);
    expect(screen.getByText('15.0 万')).toBeInTheDocument();
  });

  it('should render rating count without formatting when less than 10000', () => {
    const movieWithLowCount = { ...mockMovie, rating_count: 5000 };
    render(<MovieCard movie={movieWithLowCount} />);
    expect(screen.getByText('5000')).toBeInTheDocument();
  });

  it('should render first 3 genres', () => {
    render(<MovieCard movie={mockMovie} />);
    expect(screen.getByText('动作')).toBeInTheDocument();
    expect(screen.getByText('科幻')).toBeInTheDocument();
    expect(screen.getByText('冒险')).toBeInTheDocument();
  });

  it('should render +N for more than 3 genres', () => {
    const movieWithManyGenres = { ...mockMovie, genres: ['动作', '科幻', '冒险', '剧情', '悬疑'] };
    render(<MovieCard movie={movieWithManyGenres} />);
    expect(screen.getByText('+2')).toBeInTheDocument();
  });

  it('should not render genre section when no genres', () => {
    const movieWithoutGenres = { ...mockMovie, genres: [] };
    const { container } = render(<MovieCard movie={movieWithoutGenres} />);
    const genreContainer = container.querySelector('.flex.flex-wrap');
    expect(genreContainer).not.toBeInTheDocument();
  });

  it('should have correct Douban link', () => {
    render(<MovieCard movie={mockMovie} />);
    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', 'https://movie.douban.com/subject/1291543/');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('should render info icon button', () => {
    render(<MovieCard movie={mockMovie} />);
    const infoButton = screen.getByRole('button', { name: /查看详情/i });
    expect(infoButton).toBeInTheDocument();
  });

  it('should show tooltip when info button is clicked', () => {
    render(<MovieCard movie={mockMovie} />);
    const infoButton = screen.getByRole('button', { name: /查看详情/i });

    fireEvent.click(infoButton);

    expect(screen.getByText('作品详情')).toBeInTheDocument();
    expect(screen.getByText('评分人数: 150,000')).toBeInTheDocument();
  });

  it('should show all genres in tooltip', () => {
    render(<MovieCard movie={mockMovie} />);
    const infoButton = screen.getByRole('button', { name: /查看详情/i });

    fireEvent.click(infoButton);

    expect(screen.getByText(/全部类型: 动作, 科幻, 冒险/)).toBeInTheDocument();
  });

  it('should show updated time in tooltip', () => {
    render(<MovieCard movie={mockMovie} />);
    const infoButton = screen.getByRole('button', { name: /查看详情/i });

    fireEvent.click(infoButton);

    expect(screen.getByText(/数据更新时间:/)).toBeInTheDocument();
  });

  describe('Rating Colors', () => {
    it('should have green background for rating >= 9', () => {
      const highRatedMovie = { ...mockMovie, rating: 9.0 };
      const { container } = render(<MovieCard movie={highRatedMovie} />);
      const ratingBadge = container.querySelector('.bg-green-500');
      expect(ratingBadge).toBeInTheDocument();
    });

    it('should have blue background for rating >= 8', () => {
      const { container } = render(<MovieCard movie={mockMovie} />);
      const ratingBadge = container.querySelector('.bg-blue-500');
      expect(ratingBadge).toBeInTheDocument();
    });

    it('should have yellow background for rating >= 7', () => {
      const mediumRatedMovie = { ...mockMovie, rating: 7.5 };
      const { container } = render(<MovieCard movie={mediumRatedMovie} />);
      const ratingBadge = container.querySelector('.bg-yellow-500');
      expect(ratingBadge).toBeInTheDocument();
    });

    it('should have orange background for rating < 7', () => {
      const lowRatedMovie = { ...mockMovie, rating: 6.5 };
      const { container } = render(<MovieCard movie={lowRatedMovie} />);
      const ratingBadge = container.querySelector('.bg-orange-500');
      expect(ratingBadge).toBeInTheDocument();
    });

    it('should have gray background when rating is null', () => {
      const unratedMovie = { ...mockMovie, rating: null };
      const { container } = render(<MovieCard movie={unratedMovie} />);
      const ratingBadge = container.querySelector('.bg-gray-400');
      expect(ratingBadge).toBeInTheDocument();
    });
  });

  it('should show 无 when genres is empty in tooltip', () => {
    const movieWithoutGenres = { ...mockMovie, genres: [] };
    render(<MovieCard movie={movieWithoutGenres} />);
    const infoButton = screen.getByRole('button', { name: /查看详情/i });

    fireEvent.click(infoButton);

    expect(screen.getByText(/全部类型: 无/)).toBeInTheDocument();
  });
});
