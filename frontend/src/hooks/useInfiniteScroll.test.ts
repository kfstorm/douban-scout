import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useInfiniteScroll } from './useInfiniteScroll';

describe('useInfiniteScroll', () => {
  const mockOnLoadMore = vi.fn();
  let mockIntersectionObserver: {
    observe: ReturnType<typeof vi.fn>;
    disconnect: ReturnType<typeof vi.fn>;
    unobserve: ReturnType<typeof vi.fn>;
    trigger: (entries: IntersectionObserverEntry[]) => void;
  };

  beforeEach(() => {
    vi.clearAllMocks();

    mockIntersectionObserver = {
      observe: vi.fn(),
      disconnect: vi.fn(),
      unobserve: vi.fn(),
      trigger: vi.fn(),
    };

    globalThis.IntersectionObserver = vi.fn().mockImplementation((callback) => {
      mockIntersectionObserver.trigger = (entries: IntersectionObserverEntry[]) => {
        callback(entries, {} as IntersectionObserver);
      };
      return mockIntersectionObserver;
    }) as unknown as typeof IntersectionObserver;
  });

  it('should return loadMoreRef function', () => {
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore: mockOnLoadMore,
        hasMore: true,
        isLoading: false,
      }),
    );

    expect(result.current.loadMoreRef).toBeInstanceOf(Function);
  });

  it('should observe element when ref is set and hasMore is true', () => {
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore: mockOnLoadMore,
        hasMore: true,
        isLoading: false,
      }),
    );

    const mockElement = document.createElement('div');
    result.current.loadMoreRef(mockElement);

    expect(mockIntersectionObserver.observe).toHaveBeenCalledWith(mockElement);
  });

  it('should not observe when hasMore is false', () => {
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore: mockOnLoadMore,
        hasMore: false,
        isLoading: false,
      }),
    );

    const mockElement = document.createElement('div');
    result.current.loadMoreRef(mockElement);

    expect(mockIntersectionObserver.observe).not.toHaveBeenCalled();
  });

  it('should not observe when isLoading is true', () => {
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore: mockOnLoadMore,
        hasMore: true,
        isLoading: true,
      }),
    );

    const mockElement = document.createElement('div');
    result.current.loadMoreRef(mockElement);

    expect(mockIntersectionObserver.observe).not.toHaveBeenCalled();
  });

  it('should call onLoadMore when element intersects', () => {
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore: mockOnLoadMore,
        hasMore: true,
        isLoading: false,
      }),
    );

    const mockElement = document.createElement('div');
    result.current.loadMoreRef(mockElement);

    const mockEntry = {
      isIntersecting: true,
      target: mockElement,
      boundingClientRect: {} as DOMRectReadOnly,
      intersectionRatio: 1,
      intersectionRect: {} as DOMRectReadOnly,
      rootBounds: null,
      time: Date.now(),
    } as IntersectionObserverEntry;

    mockIntersectionObserver.trigger([mockEntry]);

    expect(mockOnLoadMore).toHaveBeenCalled();
  });

  it('should not call onLoadMore when element is not intersecting', () => {
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore: mockOnLoadMore,
        hasMore: true,
        isLoading: false,
      }),
    );

    const mockElement = document.createElement('div');
    result.current.loadMoreRef(mockElement);

    const mockEntry = {
      isIntersecting: false,
      target: mockElement,
      boundingClientRect: {} as DOMRectReadOnly,
      intersectionRatio: 0,
      intersectionRect: {} as DOMRectReadOnly,
      rootBounds: null,
      time: Date.now(),
    } as IntersectionObserverEntry;

    mockIntersectionObserver.trigger([mockEntry]);

    expect(mockOnLoadMore).not.toHaveBeenCalled();
  });

  it('should disconnect previous observer when ref changes', () => {
    const { result } = renderHook(
      ({ hasMore }) =>
        useInfiniteScroll({
          onLoadMore: mockOnLoadMore,
          hasMore,
          isLoading: false,
        }),
      {
        initialProps: { hasMore: true },
      },
    );

    const mockElement1 = document.createElement('div');
    result.current.loadMoreRef(mockElement1);

    expect(mockIntersectionObserver.observe).toHaveBeenCalledWith(mockElement1);

    const mockElement2 = document.createElement('div');
    result.current.loadMoreRef(mockElement2);

    expect(mockIntersectionObserver.disconnect).toHaveBeenCalled();
    expect(mockIntersectionObserver.observe).toHaveBeenCalledWith(mockElement2);
  });

  it('should use custom threshold', () => {
    const customThreshold = 200;
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore: mockOnLoadMore,
        hasMore: true,
        isLoading: false,
        threshold: customThreshold,
      }),
    );

    const mockElement = document.createElement('div');
    result.current.loadMoreRef(mockElement);

    expect(globalThis.IntersectionObserver).toHaveBeenCalledWith(
      expect.any(Function),
      expect.objectContaining({
        rootMargin: `${customThreshold}px`,
      }),
    );
  });

  it('should use default threshold of 100', () => {
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore: mockOnLoadMore,
        hasMore: true,
        isLoading: false,
      }),
    );

    const mockElement = document.createElement('div');
    result.current.loadMoreRef(mockElement);

    expect(globalThis.IntersectionObserver).toHaveBeenCalledWith(
      expect.any(Function),
      expect.objectContaining({
        rootMargin: '100px',
      }),
    );
  });

  it('should disconnect observer on unmount', () => {
    const { result, unmount } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore: mockOnLoadMore,
        hasMore: true,
        isLoading: false,
      }),
    );

    const mockElement = document.createElement('div');
    result.current.loadMoreRef(mockElement);
    unmount();

    expect(mockIntersectionObserver.disconnect).toHaveBeenCalled();
  });

  it('should handle null element gracefully', () => {
    const { result } = renderHook(() =>
      useInfiniteScroll({
        onLoadMore: mockOnLoadMore,
        hasMore: true,
        isLoading: false,
      }),
    );

    expect(() => {
      result.current.loadMoreRef(null);
    }).not.toThrow();
  });
});
