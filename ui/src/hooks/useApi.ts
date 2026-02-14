import { useState, useCallback } from 'react'
import type { Song, SongsListResponse, PlaylistRequest, PlaylistResponse, SearchParams, NavidromeConfig, PaginatedSearchResult } from '@/types'

const API_BASE = '/api'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export function useSearchSongs() {
  const [state, setState] = useState<UseApiState<PaginatedSearchResult>>({
    data: null,
    loading: false,
    error: null,
  })

  const search = useCallback(async (params: SearchParams): Promise<PaginatedSearchResult> => {
    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      const queryParts: string[] = []
      if (params.artist) queryParts.push(`artist=${encodeURIComponent(params.artist)}`)
      if (params.title) queryParts.push(`title=${encodeURIComponent(params.title)}`)
      if (params.album) queryParts.push(`album=${encodeURIComponent(params.album)}`)
      if (params.limit !== undefined) queryParts.push(`limit=${params.limit}`)
      if (params.offset !== undefined) queryParts.push(`offset=${params.offset}`)

      const queryString = queryParts.join('&')
      const response = await fetch(`${API_BASE}/songs/search?${queryString}`)

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`)
      }

      const data: SongsListResponse = await response.json()
      const result: PaginatedSearchResult = {
        songs: data.songs,
        total: data.total,
        limit: data.limit,
        offset: data.offset,
      }
      setState({ data: result, loading: false, error: null })
      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Search failed'
      setState({ data: null, loading: false, error: errorMessage })
      throw err
    }
  }, [])

  return { ...state, search }
}

export function useGeneratePlaylist() {
  const [state, setState] = useState<UseApiState<PlaylistResponse>>({
    data: null,
    loading: false,
    error: null,
  })

  const generate = useCallback(async (seeds: Song[], length: number = 20, bpmJitter: number = 5.0): Promise<PlaylistResponse> => {
    setState({ data: null, loading: true, error: null })

    try {
      const request: PlaylistRequest = {
        seeds: seeds.map((s) => ({
          title: s.title,
          artist: s.artist,
          album: s.album,
        })),
        length,
        bpm_jitter: bpmJitter,
        sync_to_navidrome: false,
      }

      const response = await fetch(`${API_BASE}/playlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Generation failed: ${response.statusText}`)
      }

      const data: PlaylistResponse = await response.json()
      setState({ data, loading: false, error: null })
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Playlist generation failed'
      setState({ data: null, loading: false, error: errorMessage })
      throw err
    }
  }, [])

  return { ...state, generate }
}

export function useSyncToNavidrome() {
  const [state, setState] = useState<UseApiState<{ success: boolean }>>({
    data: null,
    loading: false,
    error: null,
  })

  const sync = useCallback(async (
    playlistSongs: Song[],
    playlistName: string,
  ): Promise<boolean> => {
    setState({ data: null, loading: true, error: null })

    try {
      const navidromeConfig: NavidromeConfig = {
        playlist_name: playlistName,
      }

      const request = {
        song_ids: playlistSongs.map((s) => s.id),
        navidrome_config: navidromeConfig,
      }

      const response = await fetch(`${API_BASE}/playlist/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || `Sync failed: ${response.statusText}`)
      }

      setState({ data: { success: true }, loading: false, error: null })
      return true
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Sync to Navidrome failed'
      setState({ data: null, loading: false, error: errorMessage })
      throw err
    }
  }, [])

  return { ...state, sync }
}
