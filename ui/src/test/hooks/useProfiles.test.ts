import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useProfiles } from '@/hooks/useProfiles'
import type { Profile } from '@/types'

const mockProfile: Profile = {
  id: 1,
  display_name: 'Shared',
  subsonic_url: 'http://navidrome.local',
  subsonic_username: 'admin',
  has_subsonic_password: true,
  created_at: '2026-02-16T12:00:00',
  updated_at: '2026-02-16T12:00:00',
}

const mockProfile2: Profile = {
  id: 2,
  display_name: 'Nick',
  subsonic_url: null,
  subsonic_username: null,
  has_subsonic_password: false,
  created_at: '2026-02-16T13:00:00',
  updated_at: '2026-02-16T13:00:00',
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('useProfiles', () => {
  describe('fetchProfiles', () => {
    it('fetches profiles successfully', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => [mockProfile, mockProfile2],
      } as Response)

      const { result } = renderHook(() => useProfiles())

      await act(async () => {
        const profiles = await result.current.fetchProfiles()
        expect(profiles).toEqual([mockProfile, mockProfile2])
      })

      expect(result.current.profiles).toEqual([mockProfile, mockProfile2])
      expect(result.current.loading).toBe(false)
      expect(result.current.error).toBeNull()
    })

    it('handles fetch error', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        statusText: 'Internal Server Error',
      } as Response)

      const { result } = renderHook(() => useProfiles())

      await act(async () => {
        await expect(result.current.fetchProfiles()).rejects.toThrow(
          'Failed to fetch profiles: Internal Server Error',
        )
      })

      expect(result.current.error).toBe('Failed to fetch profiles: Internal Server Error')
      expect(result.current.loading).toBe(false)
    })
  })

  describe('createProfile', () => {
    it('creates a profile and adds it to state', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile2,
      } as Response)

      const { result } = renderHook(() => useProfiles())

      await act(async () => {
        const profile = await result.current.createProfile({
          display_name: 'Nick',
        })
        expect(profile).toEqual(mockProfile2)
      })

      expect(result.current.profiles).toContainEqual(mockProfile2)
      expect(result.current.loading).toBe(false)
    })

    it('handles 409 conflict error', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        statusText: 'Conflict',
        json: async () => ({ detail: 'Profile with name Nick already exists' }),
      } as Response)

      const { result } = renderHook(() => useProfiles())

      await act(async () => {
        await expect(
          result.current.createProfile({ display_name: 'Nick' }),
        ).rejects.toThrow('Profile with name Nick already exists')
      })

      expect(result.current.error).toBe('Profile with name Nick already exists')
    })
  })

  describe('updateProfile', () => {
    it('updates a profile in state', async () => {
      const updatedProfile = { ...mockProfile, display_name: 'Updated' }

      // First fetch to populate state
      vi.spyOn(globalThis, 'fetch')
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [mockProfile],
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => updatedProfile,
        } as Response)

      const { result } = renderHook(() => useProfiles())

      await act(async () => {
        await result.current.fetchProfiles()
      })

      await act(async () => {
        const profile = await result.current.updateProfile(1, {
          display_name: 'Updated',
        })
        expect(profile.display_name).toBe('Updated')
      })

      expect(result.current.profiles[0].display_name).toBe('Updated')
    })

    it('handles update error', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        statusText: 'Not Found',
        json: async () => ({ detail: 'Profile with ID 99 not found' }),
      } as Response)

      const { result } = renderHook(() => useProfiles())

      await act(async () => {
        await expect(
          result.current.updateProfile(99, { display_name: 'Nope' }),
        ).rejects.toThrow('Profile with ID 99 not found')
      })
    })
  })

  describe('deleteProfile', () => {
    it('removes profile from state', async () => {
      vi.spyOn(globalThis, 'fetch')
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [mockProfile, mockProfile2],
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
        } as Response)

      const { result } = renderHook(() => useProfiles())

      await act(async () => {
        await result.current.fetchProfiles()
      })

      expect(result.current.profiles).toHaveLength(2)

      await act(async () => {
        await result.current.deleteProfile(2)
      })

      expect(result.current.profiles).toHaveLength(1)
      expect(result.current.profiles[0].id).toBe(1)
    })

    it('handles 403 forbidden for shared profile', async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        statusText: 'Forbidden',
        json: async () => ({ detail: 'Cannot delete the Shared profile' }),
      } as Response)

      const { result } = renderHook(() => useProfiles())

      await act(async () => {
        await expect(result.current.deleteProfile(1)).rejects.toThrow(
          'Cannot delete the Shared profile',
        )
      })
    })
  })
})
