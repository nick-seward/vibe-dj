import { useState, useCallback, useRef, useEffect } from 'react'
import type { IndexJobResponse, JobStatusResponse } from '@/types'

const API_BASE = '/api'
const POLL_INTERVAL = 5000

interface UseIndexingState {
  jobId: string | null
  status: JobStatusResponse | null
  isIndexing: boolean
  error: string | null
}

export function useIndexing() {
  const [state, setState] = useState<UseIndexingState>({
    jobId: null,
    status: null,
    isIndexing: false,
    error: null,
  })

  const pollIntervalRef = useRef<number | null>(null)
  const onCompleteRef = useRef<((success: boolean, message: string) => void) | null>(null)

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
      pollIntervalRef.current = null
    }
  }, [])

  const pollStatus = useCallback(async (jobId: string) => {
    try {
      const response = await fetch(`${API_BASE}/status/${jobId}`)

      if (!response.ok) {
        throw new Error(`Failed to get status: ${response.statusText}`)
      }

      const data: JobStatusResponse = await response.json()
      setState((prev) => ({ ...prev, status: data }))

      if (data.status === 'completed') {
        stopPolling()
        setState((prev) => ({ ...prev, isIndexing: false, error: null }))
        onCompleteRef.current?.(true, 'Indexing completed successfully')
      } else if (data.status === 'failed') {
        stopPolling()
        setState((prev) => ({
          ...prev,
          isIndexing: false,
          error: data.error || 'Indexing failed',
        }))
        onCompleteRef.current?.(false, data.error || 'Indexing failed')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to poll status'
      // Only surface poll errors if polling has stopped (not transient failures)
      if (!pollIntervalRef.current) {
        setState((prev) => ({ ...prev, error: errorMessage }))
      }
    }
  }, [stopPolling])

  const startIndexing = useCallback(async (
    libraryPath: string,
    onComplete?: (success: boolean, message: string) => void
  ): Promise<IndexJobResponse | null> => {
    setState({
      jobId: null,
      status: null,
      isIndexing: true,
      error: null,
    })

    onCompleteRef.current = onComplete || null

    try {
      const response = await fetch(`${API_BASE}/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ library_path: libraryPath }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || `Failed to start indexing: ${response.statusText}`)
      }

      const data: IndexJobResponse = await response.json()
      setState((prev) => ({
        ...prev,
        jobId: data.job_id,
        status: {
          job_id: data.job_id,
          status: data.status,
          progress: null,
          error: null,
          started_at: null,
          completed_at: null,
        },
      }))

      // Start polling for status
      pollIntervalRef.current = window.setInterval(() => {
        pollStatus(data.job_id)
      }, POLL_INTERVAL)

      // Also poll immediately
      pollStatus(data.job_id)

      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start indexing'
      setState((prev) => ({
        ...prev,
        isIndexing: false,
        error: errorMessage,
      }))
      onCompleteRef.current?.(false, errorMessage)
      return null
    }
  }, [pollStatus])

  const cancelIndexing = useCallback(() => {
    stopPolling()
    setState({
      jobId: null,
      status: null,
      isIndexing: false,
      error: null,
    })
    onCompleteRef.current = null
  }, [stopPolling])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling()
    }
  }, [stopPolling])

  return {
    ...state,
    startIndexing,
    cancelIndexing,
  }
}
