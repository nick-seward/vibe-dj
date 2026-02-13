import { useState, useEffect, useCallback } from 'react'
import type { LibraryStats } from '@/types'

const API_BASE = '/api'

interface UseLibraryStatsState {
  stats: LibraryStats | null
  loading: boolean
  error: string | null
}

export function useLibraryStats() {
  const [state, setState] = useState<UseLibraryStatsState>({
    stats: null,
    loading: true,
    error: null,
  })

  const fetchStats = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      const response = await fetch(`${API_BASE}/library/stats`)

      if (!response.ok) {
        throw new Error(`Failed to fetch library stats: ${response.statusText}`)
      }

      const data: LibraryStats = await response.json()
      setState({ stats: data, loading: false, error: null })
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch library stats'
      setState({ stats: null, loading: false, error: errorMessage })
    }
  }, [])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  return {
    ...state,
    refetch: fetchStats,
  }
}
