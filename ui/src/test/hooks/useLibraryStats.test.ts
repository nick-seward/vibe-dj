import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useLibraryStats } from '@/hooks/useLibraryStats'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('useLibraryStats', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetches library stats on mount', async () => {
    const mockStats = {
      total_songs: 500,
      artist_count: 50,
      album_count: 80,
      total_duration: 108000,
      songs_with_features: 450,
      last_indexed: 1707782400.0,
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockStats,
    })

    const { result } = renderHook(() => useLibraryStats())

    expect(result.current.loading).toBe(true)

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(mockFetch).toHaveBeenCalledWith('/api/library/stats')
    expect(result.current.stats).toEqual(mockStats)
    expect(result.current.error).toBeNull()
  })

  it('handles fetch error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    const { result } = renderHook(() => useLibraryStats())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.stats).toBeNull()
    expect(result.current.error).toBe('Network error')
  })

  it('handles non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      statusText: 'Internal Server Error',
    })

    const { result } = renderHook(() => useLibraryStats())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.stats).toBeNull()
    expect(result.current.error).toBe('Failed to fetch library stats: Internal Server Error')
  })

  it('handles empty library stats', async () => {
    const emptyStats = {
      total_songs: 0,
      artist_count: 0,
      album_count: 0,
      total_duration: 0,
      songs_with_features: 0,
      last_indexed: null,
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => emptyStats,
    })

    const { result } = renderHook(() => useLibraryStats())

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.stats).toEqual(emptyStats)
    expect(result.current.error).toBeNull()
  })
})
