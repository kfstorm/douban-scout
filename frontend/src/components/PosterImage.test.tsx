import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PosterImage } from './PosterImage';
import * as api from '../services/api';

vi.mock('../services/api', () => ({
  getPosterProxyUrl: vi.fn((id: number) => `/api/movies/${id}/poster`),
}));

describe('PosterImage', () => {
  const defaultProps = {
    id: 1291543,
    title: '测试作品',
  };

  it('should render loading spinner initially', () => {
    render(<PosterImage {...defaultProps} />);
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('should have correct image src', () => {
    render(<PosterImage {...defaultProps} />);
    const img = screen.getByAltText('测试作品');
    expect(img).toHaveAttribute('src', '/api/movies/1291543/poster');
  });

  it('should call getPosterProxyUrl with correct id', () => {
    render(<PosterImage {...defaultProps} />);
    expect(api.getPosterProxyUrl).toHaveBeenCalledWith(1291543);
  });

  it('should show image when loaded', () => {
    render(<PosterImage {...defaultProps} />);
    const img = screen.getByAltText('测试作品');

    fireEvent.load(img);

    expect(img).toHaveClass('opacity-100');
    expect(img).not.toHaveClass('opacity-0');
  });

  it('should hide spinner when image is loaded', () => {
    render(<PosterImage {...defaultProps} />);
    const img = screen.getByAltText('测试作品');

    fireEvent.load(img);

    const spinner = document.querySelector('.animate-spin');
    expect(spinner).not.toBeInTheDocument();
  });

  it('should show error state when image fails to load', () => {
    render(<PosterImage {...defaultProps} />);
    const img = screen.getByAltText('测试作品');

    fireEvent.error(img);

    expect(screen.getByText('暂无海报')).toBeInTheDocument();
  });

  it('should show photo icon in error state', () => {
    render(<PosterImage {...defaultProps} />);
    const img = screen.getByAltText('测试作品');

    fireEvent.error(img);

    const photoIcon = document.querySelector('svg');
    expect(photoIcon).toBeInTheDocument();
  });

  it('should not show image in error state', () => {
    render(<PosterImage {...defaultProps} />);
    const img = screen.getByAltText('测试作品');

    fireEvent.error(img);

    expect(screen.queryByAltText('测试作品')).not.toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(<PosterImage {...defaultProps} className="custom-class" />);
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('custom-class');
  });

  it('should use correct aspect ratio container', () => {
    const { container } = render(<PosterImage {...defaultProps} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('relative');
    expect(wrapper).toHaveClass('overflow-hidden');
  });

  it('should have gray background while loading', () => {
    const { container } = render(<PosterImage {...defaultProps} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper).toHaveClass('bg-gray-200');
  });

  it('should hide image with opacity-0 while loading', () => {
    render(<PosterImage {...defaultProps} />);
    const img = screen.getByAltText('测试作品');
    expect(img).toHaveClass('opacity-0');
    expect(img).not.toHaveClass('opacity-100');
  });

  it('should handle multiple load events correctly', () => {
    render(<PosterImage {...defaultProps} />);
    const img = screen.getByAltText('测试作品');

    fireEvent.load(img);
    fireEvent.load(img);

    expect(screen.getByAltText('测试作品')).toBeInTheDocument();
    expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
  });

  it('should maintain error state after error', () => {
    render(<PosterImage {...defaultProps} />);
    const img = screen.getByAltText('测试作品');

    fireEvent.error(img);

    expect(screen.getByText('暂无海报')).toBeInTheDocument();
    expect(screen.queryByAltText('测试作品')).not.toBeInTheDocument();
  });
});
