import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import type { Profile, CreateProfileRequest, UpdateProfileRequest } from '@/types'
import { useProfiles } from '@/hooks/useProfiles'

const ACTIVE_PROFILE_KEY = 'vibe-dj-active-profile-id'

interface ProfileContextType {
  profiles: Profile[]
  activeProfileId: number | null
  activeProfile: Profile | null
  loading: boolean
  error: string | null
  setActiveProfileId: (id: number | null) => void
  refreshProfiles: () => Promise<void>
  createProfile: (request: CreateProfileRequest) => Promise<Profile>
  updateProfile: (profileId: number, request: UpdateProfileRequest) => Promise<Profile>
  deleteProfile: (profileId: number) => Promise<void>
}

const ProfileContext = createContext<ProfileContextType | undefined>(undefined)

function getStoredProfileId(): number | null {
  try {
    const stored = localStorage.getItem(ACTIVE_PROFILE_KEY)
    if (stored !== null) {
      const parsed = parseInt(stored, 10)
      return isNaN(parsed) ? null : parsed
    }
  } catch {
    // localStorage may be unavailable
  }
  return null
}

function storeProfileId(id: number | null): void {
  try {
    if (id !== null) {
      localStorage.setItem(ACTIVE_PROFILE_KEY, String(id))
    } else {
      localStorage.removeItem(ACTIVE_PROFILE_KEY)
    }
  } catch {
    // localStorage may be unavailable
  }
}

export function ProfileProvider({ children }: { children: ReactNode }) {
  const {
    profiles,
    loading,
    error,
    fetchProfiles,
    createProfile: hookCreateProfile,
    updateProfile: hookUpdateProfile,
    deleteProfile: hookDeleteProfile,
  } = useProfiles()

  const [activeProfileId, setActiveProfileIdState] = useState<number | null>(
    () => getStoredProfileId(),
  )

  const activeProfile = profiles.find((p) => p.id === activeProfileId) ?? null

  useEffect(() => {
    fetchProfiles().catch(() => {
      // Error is tracked in hook state
    })
  }, [fetchProfiles])

  const setActiveProfileId = useCallback((id: number | null) => {
    setActiveProfileIdState(id)
    storeProfileId(id)
  }, [])

  const refreshProfiles = useCallback(async () => {
    await fetchProfiles()
  }, [fetchProfiles])

  const createProfile = useCallback(async (request: CreateProfileRequest): Promise<Profile> => {
    return await hookCreateProfile(request)
  }, [hookCreateProfile])

  const updateProfile = useCallback(async (profileId: number, request: UpdateProfileRequest): Promise<Profile> => {
    return await hookUpdateProfile(profileId, request)
  }, [hookUpdateProfile])

  const deleteProfile = useCallback(async (profileId: number): Promise<void> => {
    await hookDeleteProfile(profileId)
    if (activeProfileId === profileId) {
      setActiveProfileId(null)
    }
  }, [hookDeleteProfile, activeProfileId, setActiveProfileId])

  return (
    <ProfileContext.Provider
      value={{
        profiles,
        activeProfileId,
        activeProfile,
        loading,
        error,
        setActiveProfileId,
        refreshProfiles,
        createProfile,
        updateProfile,
        deleteProfile,
      }}
    >
      {children}
    </ProfileContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useProfileContext() {
  const context = useContext(ProfileContext)
  if (context === undefined) {
    throw new Error('useProfileContext must be used within a ProfileProvider')
  }
  return context
}
