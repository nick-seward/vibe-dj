import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useIndexing } from '@/hooks/useIndexing'

// Mock fetch globally
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

const flushPromises = () => act(() => new Promise((r) => setTimeout(r, 0)))

describe('useIndexing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('active job detection on mount', () => {
    it('sets idle state when no active job exists', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: null,
          status: 'idle',
          progress: null,
          error: null,
          started_at: null,
          completed_at: null,
        }),
      })

      const { result } = renderHook(() => useIndexing())

      await flushPromises()

      expect(mockFetch).toHaveBeenCalledWith('/api/index/active')
      expect(result.current.isIndexing).toBe(false)
      expect(result.current.jobId).toBeNull()
    })

    it('resumes tracking when an active running job is found', async () => {
      // First call: /api/index/active returns a running job
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: 'active-123',
          status: 'running',
          progress: { phase: 'metadata', message: 'Extracting metadata (3/10)', processed: 3, total: 10 },
          error: null,
          started_at: '2026-01-01T00:00:00',
          completed_at: null,
        }),
      })

      // Second call: immediate pollStatus call to /api/status/active-123
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: 'active-123',
          status: 'running',
          progress: { phase: 'metadata', message: 'Extracting metadata (4/10)', processed: 4, total: 10 },
          error: null,
          started_at: '2026-01-01T00:00:00',
          completed_at: null,
        }),
      })

      const { result } = renderHook(() => useIndexing())

      await waitFor(() => {
        expect(result.current.isIndexing).toBe(true)
      })

      expect(result.current.jobId).toBe('active-123')
      expect(mockFetch).toHaveBeenCalledWith('/api/index/active')
    })

    it('resumes tracking when an active queued job is found', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: 'queued-456',
          status: 'queued',
          progress: null,
          error: null,
          started_at: null,
          completed_at: null,
        }),
      })

      // Immediate poll
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: 'queued-456',
          status: 'queued',
          progress: null,
          error: null,
          started_at: null,
          completed_at: null,
        }),
      })

      const { result } = renderHook(() => useIndexing())

      await waitFor(() => {
        expect(result.current.isIndexing).toBe(true)
      })

      expect(result.current.jobId).toBe('queued-456')
    })

    it('stays idle when fetch fails', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() => useIndexing())

      await flushPromises()

      expect(mockFetch).toHaveBeenCalledWith('/api/index/active')
      expect(result.current.isIndexing).toBe(false)
      expect(result.current.jobId).toBeNull()
      expect(result.current.error).toBeNull()
    })

    it('stays idle when response is not ok', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      })

      const { result } = renderHook(() => useIndexing())

      await flushPromises()

      expect(mockFetch).toHaveBeenCalledWith('/api/index/active')
      expect(result.current.isIndexing).toBe(false)
      expect(result.current.jobId).toBeNull()
    })
  })
})
