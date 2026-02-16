import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { ProfileProvider, useProfileContext } from '@/context/ProfileContext'
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

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <ProfileProvider>{children}</ProfileProvider>
)

beforeEach(() => {
  vi.restoreAllMocks()
  localStorage.clear()
})

describe('ProfileContext', () => {
  it('throws when used outside provider', () => {
    expect(() => {
      renderHook(() => useProfileContext())
    }).toThrow('useProfileContext must be used within a ProfileProvider')
  })

  it('loads profiles on mount', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => [mockProfile, mockProfile2],
    } as Response)

    const { result } = renderHook(() => useProfileContext(), { wrapper })

    // Wait for the useEffect fetch to complete
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(result.current.profiles).toEqual([mockProfile, mockProfile2])
    expect(result.current.loading).toBe(false)
  })

  it('starts with null active profile when nothing in localStorage', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => [mockProfile],
    } as Response)

    const { result } = renderHook(() => useProfileContext(), { wrapper })

    expect(result.current.activeProfileId).toBeNull()
    expect(result.current.activeProfile).toBeNull()
  })

  it('restores active profile from localStorage', async () => {
    localStorage.setItem('vibe-dj-active-profile-id', '1')

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => [mockProfile, mockProfile2],
    } as Response)

    const { result } = renderHook(() => useProfileContext(), { wrapper })

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(result.current.activeProfileId).toBe(1)
    expect(result.current.activeProfile).toEqual(mockProfile)
  })

  it('sets active profile and persists to localStorage', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => [mockProfile, mockProfile2],
    } as Response)

    const { result } = renderHook(() => useProfileContext(), { wrapper })

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    act(() => {
      result.current.setActiveProfileId(2)
    })

    expect(result.current.activeProfileId).toBe(2)
    expect(localStorage.getItem('vibe-dj-active-profile-id')).toBe('2')
  })

  it('clears active profile from localStorage when set to null', async () => {
    localStorage.setItem('vibe-dj-active-profile-id', '1')

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => [mockProfile],
    } as Response)

    const { result } = renderHook(() => useProfileContext(), { wrapper })

    act(() => {
      result.current.setActiveProfileId(null)
    })

    expect(result.current.activeProfileId).toBeNull()
    expect(localStorage.getItem('vibe-dj-active-profile-id')).toBeNull()
  })

  it('creates a profile via context', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [mockProfile],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockProfile2,
      } as Response)

    const { result } = renderHook(() => useProfileContext(), { wrapper })

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    await act(async () => {
      const created = await result.current.createProfile({
        display_name: 'Nick',
      })
      expect(created).toEqual(mockProfile2)
    })

    expect(result.current.profiles).toHaveLength(2)
  })

  it('updates a profile via context', async () => {
    const updatedProfile = { ...mockProfile, display_name: 'Updated' }

    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [mockProfile],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => updatedProfile,
      } as Response)

    const { result } = renderHook(() => useProfileContext(), { wrapper })

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    await act(async () => {
      const updated = await result.current.updateProfile(1, {
        display_name: 'Updated',
      })
      expect(updated.display_name).toBe('Updated')
    })

    expect(result.current.profiles[0].display_name).toBe('Updated')
  })

  it('deletes a profile and clears active if it was the active one', async () => {
    localStorage.setItem('vibe-dj-active-profile-id', '2')

    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [mockProfile, mockProfile2],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
      } as Response)

    const { result } = renderHook(() => useProfileContext(), { wrapper })

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(result.current.activeProfileId).toBe(2)

    await act(async () => {
      await result.current.deleteProfile(2)
    })

    expect(result.current.profiles).toHaveLength(1)
    expect(result.current.activeProfileId).toBeNull()
    expect(localStorage.getItem('vibe-dj-active-profile-id')).toBeNull()
  })

  it('activeProfile returns null when ID does not match any profile', async () => {
    localStorage.setItem('vibe-dj-active-profile-id', '999')

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => [mockProfile],
    } as Response)

    const { result } = renderHook(() => useProfileContext(), { wrapper })

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(result.current.activeProfileId).toBe(999)
    expect(result.current.activeProfile).toBeNull()
  })
})
