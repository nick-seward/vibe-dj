import { useState, useCallback } from 'react'
import type { Profile, CreateProfileRequest, UpdateProfileRequest } from '@/types'

const API_BASE = '/api'

interface UseProfilesState {
  profiles: Profile[]
  loading: boolean
  error: string | null
}

export function useProfiles() {
  const [state, setState] = useState<UseProfilesState>({
    profiles: [],
    loading: false,
    error: null,
  })

  const fetchProfiles = useCallback(async (): Promise<Profile[]> => {
    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      const response = await fetch(`${API_BASE}/profiles`)

      if (!response.ok) {
        throw new Error(`Failed to fetch profiles: ${response.statusText}`)
      }

      const data: Profile[] = await response.json()
      setState({ profiles: data, loading: false, error: null })
      return data
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch profiles'
      setState((prev) => ({ ...prev, loading: false, error: errorMessage }))
      throw err
    }
  }, [])

  const createProfile = useCallback(async (request: CreateProfileRequest): Promise<Profile> => {
    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      const response = await fetch(`${API_BASE}/profiles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to create profile: ${response.statusText}`)
      }

      const profile: Profile = await response.json()
      setState((prev) => ({
        profiles: [...prev.profiles, profile],
        loading: false,
        error: null,
      }))
      return profile
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create profile'
      setState((prev) => ({ ...prev, loading: false, error: errorMessage }))
      throw err
    }
  }, [])

  const updateProfile = useCallback(async (profileId: number, request: UpdateProfileRequest): Promise<Profile> => {
    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      const response = await fetch(`${API_BASE}/profiles/${profileId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to update profile: ${response.statusText}`)
      }

      const profile: Profile = await response.json()
      setState((prev) => ({
        profiles: prev.profiles.map((p) => (p.id === profileId ? profile : p)),
        loading: false,
        error: null,
      }))
      return profile
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update profile'
      setState((prev) => ({ ...prev, loading: false, error: errorMessage }))
      throw err
    }
  }, [])

  const deleteProfile = useCallback(async (profileId: number): Promise<void> => {
    setState((prev) => ({ ...prev, loading: true, error: null }))

    try {
      const response = await fetch(`${API_BASE}/profiles/${profileId}`, {
        method: 'DELETE',
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to delete profile: ${response.statusText}`)
      }

      setState((prev) => ({
        profiles: prev.profiles.filter((p) => p.id !== profileId),
        loading: false,
        error: null,
      }))
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete profile'
      setState((prev) => ({ ...prev, loading: false, error: errorMessage }))
      throw err
    }
  }, [])

  return {
    ...state,
    fetchProfiles,
    createProfile,
    updateProfile,
    deleteProfile,
  }
}
